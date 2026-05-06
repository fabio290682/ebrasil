#!/bin/bash
set -e

echo "==> Instalando dependências do backend..."
pip install -r backend/requirements.txt --quiet

echo "==> Instalando dependências do frontend..."
cd frontend && npm install --silent && cd ..

echo "==> Configurando ambiente de desenvolvimento..."
cat > .env << 'EOF'
ENVIRONMENT=development
DATABASE_BACKEND=sqlite
API_PREFIX=/api/v1
ALLOWED_HOSTS=localhost,127.0.0.1,*.app.github.dev
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
JWT_SECRET_KEY=dev_secret_key_codespaces
WORKERS=1
EOF

echo ""
echo "✅ Setup concluído!"
echo ""
echo "Para iniciar o sistema, abra dois terminais:"
echo ""
echo "  Terminal 1 (Backend):"
echo "    cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  Terminal 2 (Frontend):"
echo "    cd frontend && npm run dev -- --host 0.0.0.0"
echo ""
echo "  Ou use o script de teste:"
echo "    bash scripts/test-local.sh"
