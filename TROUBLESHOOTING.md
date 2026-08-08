# Troubleshooting

## Virtual environment activation fails

Create it in the current project folder:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Confirm `python -c "import sys; print(sys.executable)"` points inside `.venv`.

## `no such table: myapp_importrun`

```bash
python manage.py showmigrations myapp
python manage.py migrate
```

## Dependencies install into AppData/Roaming

The virtual environment is not active. Activate it before installing and use `python -m pip`.

## Static files look outdated

Restart the server and force-refresh the browser. In deployment, rerun `collectstatic`.

## Stripe checkout does not work

Check all three Stripe variables, use test-mode keys consistently, run Stripe CLI forwarding, and restart Django after editing `.env`.

## Importer returns fewer records

Review source limits, complete pagination flags, source availability, request errors, duplicate detection, and importer-run records. Never use `--archive-missing` with a partial import.

## Tests fail after changing Basic/Premium behavior

Update tests to assert the intended server-side access policy. Do not only hide premium evidence with CSS.
