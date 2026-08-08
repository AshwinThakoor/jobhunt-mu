PYTHON ?= python

install:
	$(PYTHON) -m pip install -r requirements.txt

check:
	$(PYTHON) manage.py check
	$(PYTHON) manage.py makemigrations --check --dry-run

test:
	$(PYTHON) manage.py test

lint:
	ruff check .

format:
	ruff format .

run:
	$(PYTHON) manage.py runserver

migrate:
	$(PYTHON) manage.py migrate
