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
    link_convite: Optional[str] = None
    membros_adicionados: Optional[List[str]] = None
    membros_com_erro: Optional[list] = None
    erro: Optional[str] = None

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
        
        # Pega o chat_id
        chat_id = None
        if hasattr(result, 'chats') and result.chats:
            chat_id = result.chats[0].id
        
        # Gera link de convite
        link_convite = "Link não disponível"
        
        if chat_id:
            # Método 1: Usando InputPeerChat
            try:
                peer = InputPeerChat(chat_id=chat_id)
                invite = await client(ExportChatInviteRequest(peer=peer))
                link_convite = invite.link
            except Exception as e1:
                # Método 2: Pegando do full_chat
                try:
                    full_chat = await client(GetFullChatRequest(chat_id=chat_id))
                    if full_chat.full_chat.exported_invite:
                        link_convite = full_chat.full_chat.exported_invite.link
                    else:
                        link_convite = f"Erro M1: {str(e1)[:30]}"
                except Exception as e2:
                    link_convite = f"Erro: {str(e1)[:25]} | {str(e2)[:25]}"
        
        membros_adicionados = [u.username or u.first_name for u in usuarios]
        
        return CriarGrupoResponse(
            success=True,
            grupo_nome=nome_grupo,
            link_convite=link_convite,
            membros_adicionados=membros_adicionados,
            membros_com_erro=membros_com_erro if membros_com_erro else None
        )
        
    except Exception as e:
        return CriarGrupoResponse(
            success=False,
            erro=str(e)
        )
    finally:
        if client:
            await client.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
