# Backend - Transparencia BR

API em FastAPI para servir dados de gastos publicos no Schema Unico.

## Como rodar

1. Criar ambiente virtual e instalar dependencias:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Subir API:

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

3. Abrir documentacao:

- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`

## Endpoints principais

- `GET /health`
- `GET /api/v1/gastos`
- `GET /api/v1/gastos/resumo`
- `GET /api/v1/gastos/top-fornecedores`
- `GET /api/v1/municipios`
- `GET /api/v1/municipios/{codigo_ibge}`
- `GET /api/v1/integracoes/portal/despesas`

## Integração Portal da Transparência

1. Cadastre sua chave em:
`http://www.portaldatransparencia.gov.br/api-de-dados/cadastrar-email`

2. Defina a variável de ambiente antes de subir a API:

```powershell
$env:PORTAL_TRANSPARENCIA_API_KEY="SUA_CHAVE_AQUI"
```

3. Teste:

```powershell
curl "http://127.0.0.1:8000/api/v1/integracoes/portal/despesas?pagina=1"
```

## Filtros de gastos

- `data_inicio=YYYY-MM-DD`
- `data_fim=YYYY-MM-DD`
- `uf=SC`
- `municipio_ibge=4205407`
- `elemento_despesa=339039`
- `fornecedor=alfa`
- `page=1`
- `page_size=20`

## Banco local

- O banco SQLite e criado automaticamente em `backend/data/transparencia.db`.
- No startup, a API popula dados iniciais se a base estiver vazia.

## Usar MongoDB

Defina as variaveis de ambiente antes de iniciar a API:

```powershell
$env:DATABASE_BACKEND="mongo"
$env:MONGODB_URL="mongodb://127.0.0.1:27017"
$env:MONGODB_DB="transparencia"
```

Ao subir a API, as colecoes e indices sao criados e o seed inicial e aplicado automaticamente se o banco estiver vazio.
