$ErrorActionPreference = "Stop"

# Defina a chave como variavel de ambiente do usuario/sistema antes de usar:
#   setx PORTAL_TRANSPARENCIA_API_KEY "SUA_CHAVE"
# ou descomente a linha abaixo para fixar localmente:
# $env:PORTAL_TRANSPARENCIA_API_KEY = "SUA_CHAVE"

$projectRoot = "d:\ebrasil"
$python = "python"

Set-Location $projectRoot
& $python "scripts\auto_fetch_portal.py" --data-inicio (Get-Date).ToString("yyyy-MM-dd") --data-fim (Get-Date).ToString("yyyy-MM-dd") --paginas 5
