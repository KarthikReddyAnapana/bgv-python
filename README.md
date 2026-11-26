# BGV Request Management System

Background verification (BGV) request tracking for PM, PMO Admin, and Super Admin roles.

## Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3, FastAPI, SQLModel, JWT (python-jose), Passlib/BCrypt |
| Database | SQLite file (`backend/data/bgverificationdb.sqlite`) |
| Frontend | React 18, Vite, Axios (hash-based routing) |

## Run locally

### Backend
```bash
cd backend
./run.ps1
```
`run.ps1` creates a virtualenv, installs dependencies, and starts uvicorn on port 8080. Manual steps:
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --port 8080
```

- API: http://localhost:8080
- Interactive API docs: http://localhost:8080/docs
- Tests: `.\.venv\Scripts\python.exe -m pytest`

### Frontend
```bash
cd frontend
npm install
npm run dev
```
App: http://localhost:5173

## Login

1. Enter PS Number
2. Select role (PM / PMO Admin / Super Admin)
3. Continue — JWT is obtained automatically in the background

Demo accounts (seeded on first run): `hr@demo.com` and `admin@demo.com` with password `Password123!`

## Project layout

```
BGV_Final_v24.0/
├── backend/     FastAPI API (SQLite)
├── frontend/    React UI
└── README.md
```
