$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendRoot = Join-Path $repoRoot 'frontend'
Set-Location -LiteralPath $frontendRoot

if (-not (Test-Path -LiteralPath (Join-Path $frontendRoot 'node_modules'))) {
  & npm.cmd install
}

& npm.cmd run dev -- --host 0.0.0.0 --port 5173
