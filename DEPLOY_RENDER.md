# Deploy no Render

Este projeto esta pronto para deploy com o arquivo `render.yaml` na raiz.

## 1) Preparar repositório

1. Suba este projeto para um repositório GitHub.
2. Garanta que `render.yaml` esteja no branch principal.

## 2) Criar Blueprint no Render

1. No Render: **New +** -> **Blueprint**.
2. Conecte o repositório.
3. O Render vai detectar e criar dois serviços:
   - `ebrasil-backend` (Web Service)
   - `ebrasil-frontend` (Static Site)
   - `ebrasil-n8n` (Web Service - Docker) **se estiver no seu `render.yaml`**

## 3) Ajustar variáveis obrigatórias

No backend (`ebrasil-backend`):
- `PORTAL_TRANSPARENCIA_API_KEY` = sua chave real
- `CORS_ORIGINS` = URL final do frontend no Render + origens locais

No frontend (`ebrasil-frontend`):
- `VITE_API_BASE_URL` = URL pública final do backend no Render

No n8n (`ebrasil-n8n`):
- `N8N_ENCRYPTION_KEY` = obrigatório (chave longa e persistente)
- `N8N_BASIC_AUTH_USER` e `N8N_BASIC_AUTH_PASSWORD` = obrigatório (não deixar aberto)
- `DB_POSTGRESDB_*` = Postgres do **n8n** (metadados de workflows/execuções)
- `OPENAI_API_KEY`, `PORTAL_TRANSPARENCIA_API_KEY`, `SLACK_WEBHOOK_URL` = conforme seus workflows

## 4) Banco de dados

Padrão no `render.yaml`: `DATABASE_BACKEND=sqlite`.

Para usar MongoDB em produção:
- `DATABASE_BACKEND=mongo`
- `MONGODB_URL=<sua connection string>`
- `MONGODB_DB=transparencia`

### Banco do n8n (separado)
O `ebrasil-n8n` precisa de um Postgres próprio (Render Postgres ou Supabase).

- Se você usar o `render.yaml` atualizado: o Blueprint cria o Postgres `ebrasil-n8n-db` e injeta `DB_POSTGRESDB_*` automaticamente via `fromDatabase`.
- Se preferir Supabase/externo: mantenha `DB_POSTGRESDB_*` como env vars manuais.

## 5) Validar

- Backend health: `https://SEU-BACKEND.onrender.com/health`
- Docs: `https://SEU-BACKEND.onrender.com/docs`
- Frontend: `https://SEU-FRONTEND.onrender.com`
- n8n: `https://SEU-N8N.onrender.com`

## 6) Pós deploy recomendado

- Trocar placeholders `SEU-FRONTEND` e `SEU-BACKEND` nas envs.
- Forçar novo deploy manual após atualizar env vars.
- Gerar segredos do n8n (uma vez) com: `powershell -ExecutionPolicy Bypass -File scripts/generate_n8n_secrets.ps1`
