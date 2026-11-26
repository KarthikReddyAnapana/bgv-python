# Run the BGV FastAPI backend on http://localhost:8080
# Usage: from the backend/ folder run  ./run.ps1
$venvPath = Join-Path $PSScriptRoot '.venv'
# Module invocation avoids pip.exe/uvicorn.exe wrappers that may retain a previous venv path.
$python = Join-Path $venvPath 'Scripts\python.exe'

if (-not (Test-Path $python)) {
    python -m venv $venvPath
}

& $python -m pip install -q -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

# Resolve .env and the relative SQLite data path from backend, regardless of the caller's folder.
Push-Location $PSScriptRoot
try {
    & $python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
} finally {
    Pop-Location
}
