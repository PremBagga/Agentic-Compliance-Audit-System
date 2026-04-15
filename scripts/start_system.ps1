$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Start-Process powershell -ArgumentList @(
  '-NoExit',
  '-ExecutionPolicy',
  'Bypass',
  '-File',
  (Join-Path $repoRoot 'start_backend.ps1')
)

Start-Sleep -Seconds 1

Start-Process powershell -ArgumentList @(
  '-NoExit',
  '-ExecutionPolicy',
  'Bypass',
  '-File',
  (Join-Path $repoRoot 'start_frontend.ps1')
)

Write-Host 'Backend: http://127.0.0.1:8000'
Write-Host 'Frontend: http://127.0.0.1:5173'
