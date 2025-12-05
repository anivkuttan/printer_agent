import os
import sys
import json
import time
import tempfile
import requests
import shutil
from dotenv import load_dotenv

load_dotenv()

VERSION = os.getenv("AGENT_VERSION", "0.0.0")
UPDATE_URL = os.getenv("UPDATE_URL")  # URL that returns latest version JSON

def check_for_updates():
    """Check server for updates"""
    if not UPDATE_URL:
        print("UPDATE_URL not set, skipping update check")
        return

    try:
        print("Checking for updates...")
        response = requests.get(UPDATE_URL, timeout=5)
        if response.status_code != 200:
            print("Failed to fetch update info")
            return

        data = response.json()
        latest_version = data.get("version")
        download_url = data.get("download_url")

        if not latest_version or not download_url:
            print("Invalid update JSON structure")
            return

        if latest_version == VERSION:
            print("Agent is up to date.")
            return

        print(f"Update available: {VERSION} → {latest_version}")
        download_and_install(download_url)

    except Exception as e:
        print("Update check failed:", e)


def download_and_install(url):
    """Download new EXE and replace running binary"""
    try:
        print("Downloading update...")
        temp_file = os.path.join(tempfile.gettempdir(), "agent_update.exe")

        with requests.get(url, stream=True) as r:
            r.raise_for_istance()
            with open(temp_file, "wb") as f:
                shutil.copyfileobj(r.raw, f)

        print("Download completed!")

        current_exe = sys.argv[0]

        # Replace EXE after exit
        updater_script = os.path.join(tempfile.gettempdir(), "update_agent.bat")
        with open(updater_script, "w") as f:
            f.write(f"""
@echo off
timeout /t 2 >nul
copy /y "{temp_file}" "{current_exe}"
start "" "{current_exe}"
del "{temp_file}"
del "%~f0"
""")

        print("Restarting with updated version...")
        os.startfile(updater_script)
        sys.exit(0)

    except Exception as e:
        print("Auto-update failed:", e)
