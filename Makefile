PYTHON = python
VENV = .venv
VENV_PYTHON = $(VENV)/bin/python
VENV_PIP = $(VENV)/bin/pip

ifeq ($(OS),Windows_NT)
	VENV_PYTHON = $(VENV)/Scripts/python.exe
	VENV_PIP = $(VENV)/Scripts/pip.exe
endif

# Create virtual environment
venv:
	$(PYTHON) -m venv $(VENV)

# Install dependencies including python-dotenv
install:
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt

# Run in development mode (DEBUG and other envs will be loaded from .env)
run-dev:
	$(VENV_PYTHON) app.py

# Run in production mode (USE_WAITRESS=true in .env will trigger waitress)
run-prod:
ifeq ($(OS),Windows_NT)
	$(VENV_PYTHON) app.py
else
	$(VENV)/bin/gunicorn -w 2 -b 127.0.0.1:5006 app:app
endif

# Clean up build artifacts and pycache
clean:
	python -c "import shutil, os, glob; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', '__pycache__']]; [os.remove(f) for f in glob.glob('**/*.pyc', recursive=True)]"

# Windows build command
build:
	.\build_agent.bat
