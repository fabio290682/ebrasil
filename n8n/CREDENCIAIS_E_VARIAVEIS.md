# Configuracao de Credenciais no n8n

## 1) Credencial Postgres (obrigatoria)
Nome sugerido: `Postgres Transparencia`
Tipo: `Postgres`

Campos:
- Host: seu host do Postgres/Supabase
- Database: base com `fontes_transparencia` e `gastos_publicos_unificados`
- User: usuario de aplicacao
- Password: senha de aplicacao
- Port: 5432
- SSL: habilitado em producao

Depois, abra cada workflow e substitua:
- `REPLACE_POSTGRES_CREDENTIAL_ID`
por essa credencial.

## 2) OpenAI API key (workflow com IA)
Workflow: `integracao_nacional_ia.json`
Node: `IA Classifica`

O node usa header:
`Authorization: Bearer {{$env.OPENAI_API_KEY}}`

Logo, basta configurar `OPENAI_API_KEY` no ambiente do n8n.

## 3) Slack Webhook (alertas)
Workflow: `alerta_falhas_fontes.json`
Node: `Slack Alerta`

Trocar URL fixa por credencial/variavel:
- recomendado: usar `{{$env.SLACK_WEBHOOK_URL}}`

## 4) Portal Transparencia API key
Se alguma fonte no workflow exigir a chave, inclua no HTTP Request:
Header:
- `chave-api-dados: {{$env.PORTAL_TRANSPARENCIA_API_KEY}}`

## 5) Checklist rapido de seguranca (producao)
- N8N_BASIC_AUTH ativo
- N8N_ENCRYPTION_KEY forte e persistente
- SSL/TLS ativo no dominio
- usuario/senha de banco sem privilegios de superuser
- backup diario da base do n8n e da base de dados unificada
