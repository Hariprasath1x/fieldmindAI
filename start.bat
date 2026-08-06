@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"

if not exist "%PYTHON%" set "PYTHON=python"

echo Starting FieldMind backend on http://localhost:8000 ...
pushd "%ROOT%"
start "FieldMind Backend" cmd /k ""%PYTHON%" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

echo Starting FieldMind frontend on http://localhost:8501 ...
start "FieldMind Frontend" cmd /k ""%PYTHON%" -m streamlit run frontend/app.py"
popd

echo.
echo FieldMind is starting.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:8501
echo.

endlocal
