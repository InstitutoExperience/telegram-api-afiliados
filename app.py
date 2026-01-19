from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.tl.functions.messages import CreateChatRequest, ExportChatInviteRequest, GetFullChatRequest
from telethon.tl.types import InputPeerChat
from telethon.sessions import StringSession
from typing import List, Optional
import os

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
    "gusthavo_x_x"
]

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
    erro: Optional[str] = None
    debug_info: Optional[str] = None

async def get_client():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        raise HTTPException(status_code=500, detail="Cliente não autorizado")
    return client

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
        
        nome_grupo = f"{request.nome_afiliado} • Experience Group"
        
        membros = []
        
        if request.adicionar_equipe_fixa:
            membros.extend(EQUIPE_FIXA)
        
        if request.membros:
            for membro in request.membros:
                username = membro.replace("@", "")
                if username and username not in membros:
                    membros.append(username)
        
        username_afiliado = request.username_afiliado.replace("@", "")
        if username_afiliado and username_afiliado not in membros:
            membros.append(username_afiliado)
        
        usuarios = []
        membros_com_erro = []
        
        for username in membros:
            try:
                user = await client.get_entity(username)
                usuarios.append(user)
            except Exception as e:
                membros_com_erro.append({"username": username, "erro": str(e)})
        
        if not usuarios:
            return CriarGrupoResponse(
                success=False,
                erro="Nenhum usuário encontrado"
            )
        
        result = await client(CreateChatRequest(
            users=usuarios,
            title=nome_grupo
        ))
        
        # Pega o chat_id - CORRIGIDO PARA OBJETO UPDATES
        chat_id = None
        debug_info = f"Result type: {type(result).__name__}"

        # Método 1: Direto de result.chats (mais comum)
        if hasattr(result, 'chats') and result.chats:
            chat_id = result.chats[0].id
            debug_info += " | via chats[0]"
        
        # Método 2: Se result.updates existe como LISTA
        elif hasattr(result, 'updates') and isinstance(result.updates, list):
            for update in result.updates:
                if hasattr(update, 'message') and hasattr(update.message, 'peer_id'):
                    if hasattr(update.message.peer_id, 'chat_id'):
                        chat_id = update.message.peer_id.chat_id
                        debug_info += " | via updates list"
                        break
        
        # Método 3: Se updates é objeto único
        elif hasattr(result, 'updates') and hasattr(result.updates, 'chats'):
            if result.updates.chats:
                chat_id = result.updates.chats[0].id
                debug_info += " | via updates.chats"
        
        # Método 4: Buscar em qualquer atributo que tenha 'chat'
        if not chat_id:
            for attr_name in dir(result):
                if 'chat' in attr_name.lower():
                    attr = getattr(result, attr_name, None)
                    if attr and hasattr(attr, '__iter__') and not isinstance(attr, str):
                        try:
                            for item in attr:
                                if hasattr(item, 'id'):
                                    chat_id = item.id
                                    debug_info += f" | via {attr_name}"
                                    break
                        except:
                            pass
                    if chat_id:
                        break
        
        # Debug: mostrar atributos disponíveis se ainda não encontrou
        if not chat_id:
            attrs = [a for a in dir(result) if not a.startswith('_')]
            debug_info += f" | attrs: {attrs[:10]}"

        # Gera link de convite
        link_convite = "Link não disponível"

        if chat_id:
            try:
                invite = await client(ExportChatInviteRequest(peer=chat_id))
                link_convite = invite.link
            except Exception as e1:
                try:
                    peer = InputPeerChat(chat_id=chat_id)
                    invite = await client(ExportChatInviteRequest(peer=peer))
                    link_convite = invite.link
                except Exception as e2:
                    try:
                        full_chat = await client(GetFullChatRequest(chat_id=chat_id))
                        if full_chat.full_chat.exported_invite:
                            link_convite = full_chat.full_chat.exported_invite.link
                    except Exception as e3:
                        link_convite = f"Erro: {str(e1)[:40]}"
        
        membros_adicionados = [u.username or u.first_name for u in usuarios]
        
        return CriarGrupoResponse(
            success=True,
            grupo_nome=nome_grupo,
            chat_id=chat_id,
            link_convite=link_convite,
            membros_adicionados=membros_adicionados,
            membros_com_erro=membros_com_erro if membros_com_erro else None,
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
