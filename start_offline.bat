@echo off
echo ===================================================================
echo       PolyGen - 100%% Offline Text-to-3D Studio Launcher
echo ===================================================================
echo.
echo No internet connection is required!
echo Generated models will be saved in: %~dp0outputs\
echo.

echo Starting PolyGen Server on http://127.0.0.1:8000...
cd /d "%~dp0backend"
call venv\Scripts\activate.bat

:: Launch the browser after 2 seconds in parallel
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000"

:: Start Uvicorn serving both Backend API and compiled Frontend
python -m uvicorn main:app --host 127.0.0.1 --port 8000

