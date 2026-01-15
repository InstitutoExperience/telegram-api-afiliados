from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.tl.functions.messages import CreateChatRequest, ExportChatInviteRequest
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import UserPrivacyRestrictedError, UserNotMutualContactError
import os
import asyncio

app = FastAPI(title="Telegram Group Creator API")

# Credenciais do Telegram (configurar como variáveis de ambiente no Railway)
API_ID = int(os.getenv("API_ID", "37578821"))
API_HASH = os.getenv("API_HASH", "0afc13452cd98aaf062b15fe07851ef0")
PHONE = os.getenv("PHONE", "")  # Número com código do país: +5511999999999
SESSION_STRING = os.getenv("SESSION_STRING", "")

# Equipe fixa que sempre entra nos grupos
EQUIPE_FIXA = [
    "peteruso",
    "marianaricarte", 
    "bruno_souusa",
    "alyssin1",
    "annymendess",
    "allanbrandao7"
]


class CriarGrupoRequest(BaseModel):
    nome_afiliado: str
    username_afiliado: str
    membro_extra: str = None  # Opcional


class CriarGrupoResponse(BaseModel):
    success: bool
    grupo_nome: str = None
    link_convite: str = None
    membros_adicionados: list = None
    membros_com_erro: list = None
    erro: str = None


async def get_client():
    """Cria e retorna o cliente Telethon"""
    if SESSION_STRING:
        from telethon.sessions import StringSession
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    else:
        client = TelegramClient('session', API_ID, API_HASH)
    
    await client.connect()
    
    if not await client.is_user_authorized():
        raise HTTPException(
            status_code=500, 
            detail="Cliente não autorizado. Configure o SESSION_STRING."
        )
    
    return client


@app.get("/")
async def root():
    return {"status": "online", "message": "API Telegram Group Creator"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/criar-grupo", response_model=CriarGrupoResponse)
async def criar_grupo(request: CriarGrupoRequest):
    """
    Cria um grupo no Telegram com o afiliado + equipe fixa
    """
    client = None
    try:
        client = await get_client()
        
        # Nome do grupo
        nome_grupo = f"{request.nome_afiliado} - Suporte Afiliado"
        
        # Lista de membros a adicionar
        membros = EQUIPE_FIXA.copy()
        
        # Adiciona o afiliado
        username_afiliado = request.username_afiliado.replace("@", "")
        membros.append(username_afiliado)
        
        # Adiciona membro extra se informado
        if request.membro_extra and request.membro_extra.lower() not in ["não", "nao", "n", "-"]:
            membro_extra = request.membro_extra.replace("@", "")
            membros.append(membro_extra)
        
        # Resolve os usernames para entidades
        usuarios_para_adicionar = []
        membros_com_erro = []
        
        for username in membros:
            try:
                user = await client.get_entity(username)
                usuarios_para_adicionar.append(user)
            except Exception as e:
                membros_com_erro.append({"username": username, "erro": str(e)})
        
        if not usuarios_para_adicionar:
            return CriarGrupoResponse(
                success=False,
                erro="Não foi possível encontrar nenhum usuário para adicionar ao grupo"
            )
        
        # Cria o grupo (chat normal, não supergrupo)
        result = await client(CreateChatRequest(
            users=usuarios_para_adicionar,
            title=nome_grupo
        ))
        
        # Pega o ID do chat criado
        chat_id = result.chats[0].id
        
        # Gera link de convite
        try:
            invite = await client(ExportChatInviteRequest(peer=chat_id))
            link_convite = invite.link
        except Exception as e:
            link_convite = f"Erro ao gerar link: {str(e)}"
        
        # Lista de membros adicionados com sucesso
        membros_adicionados = [u.username or u.first_name for u in usuarios_para_adicionar]
        
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


@app.post("/adicionar-membro")
async def adicionar_membro(grupo_link: str, username: str):
    """
    Adiciona um membro a um grupo existente
    """
    client = None
    try:
        client = await get_client()
        
        username = username.replace("@", "")
        user = await client.get_entity(username)
        
        # Pega o grupo pelo link
        grupo = await client.get_entity(grupo_link)
        
        await client(InviteToChannelRequest(
            channel=grupo,
            users=[user]
        ))
        
        return {"success": True, "message": f"@{username} adicionado com sucesso"}
        
    except UserPrivacyRestrictedError:
        return {"success": False, "erro": "Usuário tem privacidade restrita"}
    except UserNotMutualContactError:
        return {"success": False, "erro": "Usuário precisa ser contato mútuo"}
    except Exception as e:
        return {"success": False, "erro": str(e)}
    finally:
        if client:
            await client.disconnect()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
