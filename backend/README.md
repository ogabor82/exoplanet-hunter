# Exoplanet Hunter backend

Minimal FastAPI backend skeleton for the Exoplanet Hunter research application.

## Local setup

Python 3.11 or newer is required. From the `backend` directory, create and
activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

Install the project and its dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

## Run the development server

From the `backend` directory, with the virtual environment active:

```bash
uvicorn app.main:app --reload
```

The API will be available at <http://127.0.0.1:8000>.
