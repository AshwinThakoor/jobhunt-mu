@echo off
call .venv-jobhunt\Scripts\activate.bat
python scrape_jobs.py --django --download-images --myjob-all --archive-missing
python manage.py archive_stale_jobs --days 14
pause
