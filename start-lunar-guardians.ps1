param(
  [switch]$OpenBrowser = $true
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$python = Join-Path $backend 'venv\Scripts\python.exe'

function Test-HttpEndpoint([string]$url) {
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
  } catch {
    return $false
  }
}

if (-not (Test-Path $python)) {
  throw "Backend virtual environment not found at $python. Create it and install backend\requirements.txt first."
}

if (-not (Test-HttpEndpoint 'http://127.0.0.1:8000/health')) {
  Start-Process `
    -FilePath $python `
    -WorkingDirectory $backend `
    -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000' `
    -WindowStyle Normal | Out-Null
}

$backendReady = $false
for ($attempt = 1; $attempt -le 30; $attempt++) {
  if (Test-HttpEndpoint 'http://127.0.0.1:8000/health') {
    $backendReady = $true
    break
  }
  Start-Sleep -Milliseconds 500
}

if (-not $backendReady) {
  throw 'FastAPI backend did not become ready at http://127.0.0.1:8000/health.'
}

if (-not (Test-HttpEndpoint 'http://127.0.0.1:5173')) {
  Start-Process `
    -FilePath 'npm.cmd' `
    -WorkingDirectory $frontend `
    -ArgumentList 'run', 'dev', '--', '--host', '127.0.0.1' `
    -WindowStyle Normal | Out-Null
}

$frontendReady = $false
for ($attempt = 1; $attempt -le 30; $attempt++) {
  if (Test-HttpEndpoint 'http://127.0.0.1:5173') {
    $frontendReady = $true
    break
  }
  Start-Sleep -Milliseconds 500
}

if (-not $frontendReady) {
  throw 'Frontend did not become ready at http://127.0.0.1:5173.'
}

Write-Host 'LUNAR GUARDIANS is ready.'
Write-Host 'Frontend: http://127.0.0.1:5173'
Write-Host 'Backend:  http://127.0.0.1:8000/docs'

if ($OpenBrowser) {
  Start-Process 'http://127.0.0.1:5173'
}
