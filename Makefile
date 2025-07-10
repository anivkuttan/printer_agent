PYTHON = python
VENV = .venv
VENV_PYTHON = $(VENV)/bin/python
VENV_PIP = $(VENV)/bin/pip

ifeq ($(OS),Windows_NT)
	VENV_PYTHON = $(VENV)/Scripts/python.exe
	VENV_PIP = $(VENV)/Scripts/pip.exe
endif

venv:
	$(PYTHON) -m venv $(VENV)

install:
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt

run-dev:
	$(VENV_PYTHON) -m src.app

run-prod:
ifeq ($(OS),Windows_NT)
	$(VENV_PYTHON) -c "from src.app import app; from waitress import serve; serve(app, host='127.0.0.1', port=5005)"
else
	$(VENV)/bin/gunicorn -w 2 -b 127.0.0.1:5005 src.app:app
endif

clean:
	python -c "import shutil, os, glob; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', '__pycache__']]; [os.remove(f) for f in glob.glob('**/*.pyc', recursive=True)]"

build:
	.\build_agent.bat