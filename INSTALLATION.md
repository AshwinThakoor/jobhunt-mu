# Installation

## Prerequisites

- Python 3.12 or 3.13
- Git
- Optional: Docker Desktop
- Optional: Stripe CLI for local webhook testing

## Local installation

```bash
git clone https://github.com/AshwinThakoor/jobhunt-mu.git
cd jobhunt-mu
python -m venv .venv
```

Activate the environment and install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py check
python manage.py test
python manage.py runserver
```

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Initial administrator

```bash
python manage.py createsuperuser
```

Open `/admin/` after starting the server.

## Verification

```bash
python -c "import django, pandas, stripe, PIL; print('Dependencies OK')"
python -m pip check
python manage.py showmigrations
python manage.py test
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common failures.
