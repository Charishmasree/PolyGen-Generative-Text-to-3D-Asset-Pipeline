@echo off
echo ===================================================================
echo             PolyGen - AI Text-to-3D Model Generation
echo ===================================================================
echo.

echo [1/2] Starting FastAPI Backend on http://localhost:8000...
start "PolyGen Backend (FastAPI)" cmd /k "cd backend && call venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting React + Vite Frontend on http://localhost:5173...
start "PolyGen Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are starting up!
echo - Web Dashboard: http://localhost:5173
echo - Backend API Docs: http://localhost:8000/docs
echo ===================================================================
pause

