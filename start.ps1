param()

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $root

Write-Host "Checking Python environment..."
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

$python = Join-Path $root ".venv\Scripts\python.exe"
$pip = Join-Path $root ".venv\Scripts\pip.exe"

if (-not (Test-Path $python)) {
    $python = "python"
    $pip = "pip"
}

Write-Host "Installing backend dependencies..."
& $pip install -r requirements.txt

Write-Host "Checking Node.js environment..."
Set-Location -Path "frontend"
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    & npm.cmd install
}
Set-Location -Path $root

$backendProcess = $null
$frontendProcess = $null

try {
    Write-Host "Starting FieldMind backend on http://localhost:8002 ..."
    $backendProcess = Start-Process -FilePath $python -ArgumentList "-m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8002" -NoNewWindow -PassThru

    Write-Host "Starting FieldMind frontend (Vite) on port 5174 ..."
    $frontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev -- --port 5174" -WorkingDirectory "$root\frontend" -NoNewWindow -PassThru

    Write-Host ""
    Write-Host "FieldMind is starting."
    Write-Host "Backend:  http://localhost:8002"
    Write-Host "Frontend: http://localhost:5174"
    Write-Host ""
    Write-Host "Press Ctrl+C to stop both processes."

    # Wait indefinitely until Ctrl+C
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "Stopping FieldMind..."
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($frontendProcess -and -not $frontendProcess.HasExited) {
        # taskkill is needed to kill the node subprocess tree spawned by npm
        taskkill /PID $frontendProcess.Id /T /F 2>$null
    }
}
