$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $repoRoot

$pythonExe = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
  throw "Python virtual environment not found at $pythonExe"
}

& $pythonExe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
