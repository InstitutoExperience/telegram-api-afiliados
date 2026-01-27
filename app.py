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
    """Busca usuário por user
