@echo off
set PORTAL_TRANSPARENCIA_API_KEY=COLE_SUA_CHAVE_AQUI
python scripts\auto_fetch_portal.py --loop --interval-min 60 --paginas 5
