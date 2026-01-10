# Echo

Echo is a lightweight full-stack app with a FastAPI backend and a Vite + React frontend for quick local development.

## Backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn
python main.py
```

API: http://localhost:8000

## Frontend (Vite)

```powershell
cd frontend
npm install
npm run dev
```

Web: http://localhost:5173
