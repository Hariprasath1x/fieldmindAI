@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"

if not exist "%PYTHON%" set "PYTHON=python"

echo Starting FieldMind backend on http://localhost:8002 ...
pushd "%ROOT%"
start "FieldMind Backend" cmd /k ""%PYTHON%" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8002"

echo Starting FieldMind React frontend on http://localhost:5173 ...
pushd "%ROOT%frontend"
start "FieldMind Frontend" cmd /k "npm run dev"
popd
popd

echo.
echo FieldMind is starting.
echo Backend:  http://localhost:8002
echo Frontend: http://localhost:5173
echo.

endlocal
