@echo off
title eBrasil — Transparencia BR
color 0A

echo.
echo  ==========================================
echo   eBrasil - Transparencia BR v2.0.0
echo  ==========================================
echo.

:: Verifica Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado. Instale em python.org
    pause
    exit /b 1
)

:: Verifica Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Node.js nao encontrado. Instale em nodejs.org
    pause
    exit /b 1
)

:: Instala dependencias do backend se necessario
echo [1/4] Verificando dependencias do backend...
cd backend
pip install -r requirements.txt -q --disable-pip-version-check
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar dependencias Python
    pause
    exit /b 1
)
cd ..

:: Instala dependencias do frontend se necessario
echo [2/4] Verificando dependencias do frontend...
cd frontend
if not exist "node_modules" (
    echo      Instalando node_modules...
    npm install --silent
)
cd ..

:: Cria .env se nao existir
if not exist ".env" (
    echo [3/4] Criando arquivo .env...
    (
        echo DATABASE_BACKEND=sqlite
        echo ENVIRONMENT=development
        echo JWT_SECRET_KEY=dev_local_key_change_in_production
        echo ALLOWED_HOSTS=localhost,127.0.0.1
        echo CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
        echo API_PREFIX=/api/v1
        echo WORKERS=1
    ) > .env
) else (
    echo [3/4] Arquivo .env ja existe.
)

echo [4/4] Iniciando servidores...
echo.
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo.
echo  Pressione Ctrl+C em cada janela para parar.
echo.

:: Inicia backend em nova janela
start "Backend - eBrasil" cmd /k "cd /d %~dp0backend && set DATABASE_BACKEND=sqlite && set ENVIRONMENT=development && set JWT_SECRET_KEY=dev_local_key && set ALLOWED_HOSTS=localhost,127.0.0.1 && set CORS_ORIGINS=http://localhost:5173 && set API_PREFIX=/api/v1 && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000 --log-level info"

:: Aguarda backend iniciar
timeout /t 3 /nobreak >nul

:: Inicia frontend em nova janela
start "Frontend - eBrasil" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Abre browser
timeout /t 4 /nobreak >nul
start http://localhost:5173

echo  Servidores iniciados! O browser vai abrir automaticamente.
echo  Para parar: feche as janelas "Backend" e "Frontend".
echo.
pause
