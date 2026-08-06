param()

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    $python = "python"
}

Write-Host "Starting FieldMind backend on http://localhost:8000 ..."
Start-Process -FilePath $python -ArgumentList @(
    "-m", "uvicorn", "backend.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"
) -WorkingDirectory $root

Write-Host "Starting FieldMind frontend on http://localhost:8501 ..."
Start-Process -FilePath $python -ArgumentList @(
    "-m", "streamlit", "run", "frontend/app.py"
) -WorkingDirectory $root

Write-Host ""
Write-Host "FieldMind is starting."
Write-Host "Backend:  http://localhost:8000"
Write-Host "Frontend: http://localhost:8501"
Write-Host ""
