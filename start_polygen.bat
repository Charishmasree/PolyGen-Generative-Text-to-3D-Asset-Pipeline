@echo off
echo ===================================================================
echo             PolyGen - AI Text-to-3D Model Generation
echo ===================================================================
echo.
if not exist "outputs" mkdir outputs

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000...
start "PolyGen Backend (FastAPI)" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate.bat && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting React + Three.js Frontend on http://localhost:5173...
start "PolyGen Frontend (Vite)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: Open the browser after 3 seconds
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5173"

echo.
echo Both servers started!
echo - Web Dashboard: http://localhost:5173 (or http://127.0.0.1:8000)
echo - Generated Models Folder: "%~dp0outputs\"
echo ===================================================================
pause
