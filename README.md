# API Telegram - Criador de Grupos para Afiliados

API Python que cria grupos no Telegram usando Telethon.

## Arquivos

- `app.py` - API principal (FastAPI + Telethon)
- `requirements.txt` - Dependências Python
- `Procfile` - Configuração para Railway
- `gerar_sessao.py` - Script para gerar SESSION_STRING

## Como usar

### 1. Gerar SESSION_STRING (fazer uma vez)

No seu computador:

```bash
pip install telethon
python gerar_sessao.py
```

Siga as instruções e guarde o SESSION_STRING gerado.

### 2. Deploy no Railway

1. Crie um repositório no GitHub com esses arquivos
2. Conecte no Railway
3. Configure as variáveis de ambiente:
   - `API_ID`: 37578821
   - `API_HASH`: 0afc13452cd98aaf062b15fe07851ef0
   - `SESSION_STRING`: (string gerada no passo anterior)

### 3. Endpoints da API

**GET /** - Status da API

**GET /health** - Health check

**POST /criar-grupo** - Cria um grupo
```json
{
  "nome_afiliado": "João Silva",
  "username_afiliado": "@joaosilva",
  "membro_extra": "@outro_usuario"  // opcional
}
```

Resposta:
```json
{
  "success": true,
  "grupo_nome": "João Silva - Suporte Afiliado",
  "link_convite": "https://t.me/+xxxxx",
  "membros_adicionados": ["peteruso", "marianaricarte", ...],
  "membros_com_erro": null
}
```

## Equipe fixa

Os seguintes usuários são adicionados automaticamente em todos os grupos:
- @peteruso
- @marianaricarte
- @bruno_souusa
- @alyssin1
- @annymendess
- @allanbrandao7
