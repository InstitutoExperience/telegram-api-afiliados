"""
Script para gerar o SESSION_STRING do Telethon
Execute este script UMA VEZ no seu computador para gerar a sessão

Como usar:
1. Instale: pip install telethon
2. Execute: python gerar_sessao.py
3. Digite o número de telefone quando pedir
4. Digite o código que o Telegram enviar
5. Copie o SESSION_STRING gerado e cole no Railway
"""

from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio

# Suas credenciais
API_ID = 37578821
API_HASH = "0afc13452cd98aaf062b15fe07851ef0"

async def main():
    print("=" * 50)
    print("GERADOR DE SESSION_STRING")
    print("=" * 50)
    print()
    
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("Conectando...")
        await client.start()
        
        print()
        print("=" * 50)
        print("SESSION_STRING GERADO COM SUCESSO!")
        print("=" * 50)
        print()
        print("Copie a string abaixo (é tudo uma linha só):")
        print()
        print(client.session.save())
        print()
        print("=" * 50)
        print("Cole essa string na variável SESSION_STRING no Railway")
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
