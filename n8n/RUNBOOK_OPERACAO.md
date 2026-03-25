# Operacao - Dev e Producao

## Dev (local)
1. Copie `n8n/.env.dev.example` para `.env` no ambiente do n8n.
2. Suba n8n + Postgres.
3. Rode SQL:
   - `n8n/sql/schema_postgres.sql`
   - `n8n/sql/migration_002_agentes_publicos.sql`
   - `n8n/sql/migration_003_ia_enriquecimento.sql`
4. Importe workflows:
   - `integracao_nacional_dinamica.json`
   - `integracao_politicos_federal.json`
   - `integracao_nacional_ia.json`
   - `alerta_falhas_fontes.json`
5. Configure credencial Postgres e variaveis.
6. Execute manualmente uma vez cada workflow e valide inserts.

## Producao
1. Copie `n8n/.env.prod.example` para `.env` do servidor.
2. Configure DNS + HTTPS para n8n.
3. Aplique migrations no banco de producao.
4. Importe workflows em modo inativo.
5. Configure credenciais e IDs.
6. Faça teste manual com janela controlada (1 execucao).
7. Ative workflows gradualmente:
   - Primeiro `integracao_nacional_dinamica`
   - Depois `integracao_politicos_federal`
   - Depois `integracao_nacional_ia`
8. Ative `alerta_falhas_fontes` por ultimo.

## Validacoes pos-ativacao
- Volume de registros inseridos por execucao
- Taxa de erro por fonte
- Tempo medio de execucao
- Distribuicao de `risco_ia` (sanidade)
- Alertas no Slack funcionando
