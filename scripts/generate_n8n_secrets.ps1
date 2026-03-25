param(
  [int]$PasswordLength = 32
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-RandomHex([int]$Bytes) {
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  $data = New-Object byte[] $Bytes
  $rng.GetBytes($data)
  ($data | ForEach-Object { $_.ToString("x2") }) -join ""
}

function New-RandomPassword([int]$Length) {
  if ($Length -lt 16) { throw "PasswordLength deve ser >= 16" }
  $alphabet = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%*_-+=?"
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  $bytes = New-Object byte[] $Length
  $rng.GetBytes($bytes)
  $chars = for ($i = 0; $i -lt $Length; $i++) {
    $alphabet[ $bytes[$i] % $alphabet.Length ]
  }
  -join $chars
}

$basicUser = "admin"
$basicPass = New-RandomPassword -Length $PasswordLength

# n8n recomenda uma chave de criptografia persistente; 32+ chars.
# Aqui geramos 32 bytes => 64 chars hex.
$encryptionKey = New-RandomHex -Bytes 32

Write-Output "N8N_BASIC_AUTH_USER=$basicUser"
Write-Output "N8N_BASIC_AUTH_PASSWORD=$basicPass"
Write-Output "N8N_ENCRYPTION_KEY=$encryptionKey"
