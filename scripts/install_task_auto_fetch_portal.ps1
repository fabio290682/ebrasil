$ErrorActionPreference = "Stop"

$taskName = "Transparencia-AutoFetch-0200"
$taskPath = "\Transparencia\"
$xmlPath = "d:\ebrasil\scripts\task_auto_fetch_portal_0200.xml"

if (-not (Test-Path $xmlPath)) {
  throw "Arquivo XML nao encontrado: $xmlPath"
}

$xml = Get-Content -Path $xmlPath | Out-String

try {
  Unregister-ScheduledTask -TaskName $taskName -TaskPath $taskPath -Confirm:$false -ErrorAction SilentlyContinue
} catch {
}

Register-ScheduledTask -TaskName $taskName -TaskPath $taskPath -Xml $xml | Out-Null
Write-Output "Tarefa registrada: $taskPath$taskName"
Write-Output "Horario: diariamente as 02:00"
