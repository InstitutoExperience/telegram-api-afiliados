from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.tl.functions.messages import CreateChatRequest, ExportChatInviteRequest, GetFullChatRequest, EditChatAdminRequest
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPeerChat, User, InputPhoneContact
from telethon.sessions import StringSession
from typing import List, Optional
import os
import random

app = FastAPI(title="Telegram Group Creator API")

API_ID = int(os.getenv("API_ID", "37578821"))
API_HASH = os.getenv("API_HASH", "0afc13452cd98aaf062b15fe07851ef0")
SESSION_STRING = os.getenv("SESSION_STRING", "")

EQUIPE_FIXA = [
    "peteruso",
    "marianaricarte", 
    "bruno_souusa",
    "alyssin1",
    "annymendess",
    "allanbrandao7",
    "gusthavo_x_x",
    "gustavoczar",
    "magaffiliatesupport",
    "gabrielm_topg"
]

# Admin padrão do grupo
ADMIN_PADRAO = "bruno_souusa"

class CriarGrupoRequest(BaseModel):
    nome_afiliado: str
    username_afiliado: str
    membros: Optional[List[str]] = None
    adicionar_equipe_fixa: Optional[bool] = False

class CriarGrupoResponse(BaseModel):
    success: bool
    grupo_nome: Optional[str] = None
    chat_id: Optional[int] = None
    link_convite: Optional[str] = None
    membros_adicionados: Optional[List[str]] = None
    membros_com_erro: Optional[list] = None
    admin_promovido: Optional[str] = None
    erro: Optional[str] = None
    debug_info: Optional[str] = None

async def get_client():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        raise HTTPException(status_code=500, detail="Cliente não autorizado")
    return client

async def get_user_by_phone(client, phone_number):
    """Busca usuário pelo número de telefone"""
    try:
        contact = InputPhoneContact(
            client_id=random.randint(0, 9999999),
            phone=phone_number,
            first_name="Temp",
            last_name="User"
        )
        result = await client(ImportContactsRequest([contact]))
        
        if result.users:
            user = result.users[0]
            await client(DeleteContactsRequest(id=[user.id]))
            return user
        return None
    except Exception as e:
        print(f"Erro ao buscar por telefone {phone_number}: {e}")
        return None

async def get_user_by_identifier(client, identifier):
    """Busca usuário por username ou número de telefone"""
    identifier = identifier.strip()
    
    if identifier.startswith("@"):
        identifier = identifier[1:]
    
    clean_number = identifier.replace("+", "").replace(" ", "").replace("-", "")
    
    if clean_number.isdigit() and len(clean_number) >= 10:
        phone = identifier if identifier.startswith("+") else f"+{clean_number}"
        user = await get_user_by_phone(client, phone)
        if user:
            return user, "phone"
        else:
            return None, f"Número {phone} não encontrado no Telegram"
    else:
        try:
            user = await client.get_entity(identifier)
            if isinstance(user, User):
                return user, "username"
            else:
                return None, f"@{identifier} não é um usuário"
        except Exception as e:
            return None, str(e)

@app.get("/")
async def root():
    return {"status": "online", "message": "API Telegram Group Creator"}

@app.get("/equipe-fixa")
async def listar_equipe():
    return {"equipe_fixa": EQUIPE_FIXA}

@app.post("/criar-grupo", response_model=CriarGrupoResponse)
async def criar_grupo(request: CriarGrupoRequest):
    client = None
    try:
        client = await get_client()
        
        nome_grupo = f"{request.nome_afiliado} <> Experience Group"
        
        membros = []
        
        if request.adicionar_equipe_fixa:
            membros.extend(EQUIPE_FIXA)
        
        if request.membros:
            for membro in request.membros:
                membro_limpo = membro.replace("@", "").strip()
                if membro_limpo and membro_limpo not in membros:
                    membros.append(membro_limpo)
        
        username_afiliado = request.username_afiliado.replace("@", "").strip()
        if username_afiliado and username_afiliado not in membros:
            membros.append(username_afiliado)
        
        usuarios = []
        membros_com_erro = []
        usuario_admin = None  # Para guardar o usuário que será admin
        
        for membro in membros:
            user, result = await get_user_by_identifier(client, membro)
            if user:
                usuarios.append(user)
                # Guarda o usuário admin
                if membro.lower() == ADMIN_PADRAO.lower():
                    usuario_admin = user
            else:
                membros_com_erro.append({"identificador": membro, "erro": result})
        
        if not usuarios:
            return CriarGrupoResponse(
                success=False,
                erro="Nenhum usuário válido encontrado",
                membros_com_erro=membros_com_erro
            )
        
        result = await client(CreateChatRequest(
            users=usuarios,
            title=nome_grupo
        ))
        
        # Pega o chat_id - MÚLTIPLAS FORMAS
        chat_id = None
        debug_info = f"Result type: {type(result).__name__}"

        # Método 1: result.chats
        if hasattr(result, 'chats') and result.chats:
            chat_id = result.chats[0].id
            debug_info += " | via chats[0]"
        
        # Método 2: result.updates.chats
        elif hasattr(result, 'updates') and hasattr(result.updates, 'chats') and result.updates.chats:
            chat_id = result.updates.chats[0].id
            debug_info += " | via updates.chats"
        
        # Método 3: Buscar nos dialogs recentes
        if not chat_id:
            debug_info += " | Buscando nos dialogs..."
            async for dialog in client.iter_dialogs(limit=5):
                if dialog.name == nome_grupo:
                    chat_id = dialog.id
                    debug_info += f" | Encontrado via dialogs: {chat_id}"
                    break
        
        # Método 4: Se ainda não encontrou, buscar pela entidade do nome
        if not chat_id:
            try:
                chat_entity = await client.get_entity(nome_grupo)
                chat_id = chat_entity.id
                debug_info += f" | via get_entity: {chat_id}"
            except Exception as e:
                debug_info += f" | get_entity falhou: {str(e)[:30]}"

        # Gerenciar admins do grupo
        admin_promovido = None
        if chat_id:
            try:
                # Promover bruno_souusa como admin
                if usuario_admin:
                    await client(EditChatAdminRequest(
                        chat_id=chat_id,
                        user_id=usuario_admin,
                        is_admin=True
                    ))
                    admin_promovido = ADMIN_PADRAO
                    debug_info += f" | Admin promovido: {ADMIN_PADRAO}"
                
                # Remover você (o criador) como admin
                me = await client.get_me()
                await client(EditChatAdminRequest(
                    chat_id=chat_id,
                    user_id=me,
                    is_admin=False
                ))
                debug_info += " | Criador removido como admin"
                
            except Exception as e:
                debug_info += f" | Erro ao gerenciar admins: {str(e)[:50]}"

        # Gera link de convite
        link_convite = "Link não disponível"

        if chat_id:
            # Tenta diferentes métodos para gerar o link
            try:
                # Método 1: Direto com chat_id
                peer = InputPeerChat(chat_id=chat_id)
                invite = await client(ExportChatInviteRequest(peer=peer))
                link_convite = invite.link
            except Exception as e1:
                debug_info += f" | ExportChat erro: {str(e1)[:30]}"
                try:
                    # Método 2: Via GetFullChat
                    full_chat = await client(GetFullChatRequest(chat_id=chat_id))
                    if full_chat.full_chat.exported_invite:
                        link_convite = full_chat.full_chat.exported_invite.link
                    else:
                        # Tenta exportar novamente
                        invite = await client(ExportChatInviteRequest(peer=InputPeerChat(chat_id=chat_id)))
                        link_convite = invite.link
                except Exception as e2:
                    debug_info += f" | FullChat erro: {str(e2)[:30]}"
                    try:
                        # Método 3: Busca a entidade e exporta
                        chat_entity = await client.get_input_entity(chat_id)
                        invite = await client(ExportChatInviteRequest(peer=chat_entity))
                        link_convite = invite.link
                    except Exception as e3:
                        link_convite = f"Erro ao gerar link"
                        debug_info += f" | Todos métodos falharam"
        
        membros_adicionados = [u.username or u.phone or u.first_name for u in usuarios]
        
        return CriarGrupoResponse(
            success=True,
            grupo_nome=nome_grupo,
            chat_id=chat_id,
            link_convite=link_convite,
            membros_adicionados=membros_adicionados,
            membros_com_erro=membros_com_erro if membros_com_erro else None,
            admin_promovido=admin_promovido,
            debug_info=debug_info
        )
        
    except Exception as e:
        import traceback
        return CriarGrupoResponse(
            success=False,
            erro=str(e),
            debug_info=traceback.format_exc()[:500]
        )
    finally:
        if client:
            await client.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
