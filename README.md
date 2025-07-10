# 🧺 Laundry Printer Agent

This is a lightweight Windows-based agent that runs a local Flask server to receive print requests (PDF or terminal-style) and send them to connected printers. It includes a system tray icon and an installer built using PyInstaller + Inno Setup.

---

## 📦 Features

- Print PDF or terminal-style (RAW) text to any local/network printer.
- Choose printer by name.
- Auto-detect available and default printers.
- Minimal UI via system tray icon.
- Installer and auto-start capable.
- `.env` configurable.

---

## 🛠 Requirements

- Windows OS
- Python 3.11+
- [Inno Setup 6](https://jrsoftware.org/isinfo.php)
- [Git (optional)](https://git-scm.com/)

---

## 🚀 Setup & Run (Development Mode)

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd printer_agent
```

### 2. Create virtual environment

```bash
python -m venv .venv
call .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env` file

```env
# .env
FLASK_ENV=production
PORT=5001
DEBUG=false
INNO_COMPILER_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
```

### 5. Run the agent (dev mode)

```bash
python -m src.app
```

---

## 🧪 Test Endpoints

- `GET /ping` – Check if agent is alive
- `GET /version` – Returns version
- `GET /get-printers` – Lists printers + default
- `POST /printers` – Sends a print job (PDF or terminal)

---

## 🏗 Build Standalone EXE + Installer

### Run the build script:

```bash
build_agent.bat
```

This will:
- Compile the `.exe` using PyInstaller
- Generate an installer using Inno Setup
- Output both into the `dist/` folder

> ✅ Output:
> - `dist\laundry_printer_agent.exe`
> - `dist\LAUNDRYPrinterAgentInstaller.exe`

---

## 🖨 API: Example Print Payload

```json
POST /printers
Content-Type: application/json

{
  "printer_name": "HP LaserJet M129",
  "data_type": "pdf",
  "printer_data": "<Base64 encoded PDF>"
}
```

For terminal text:
```json
{
  "printer_name": "Thermal POS",
  "data_type": "terminal",
  "printer_data": "Hello World!\nOrder #123"
}
```

---

## 💡 Tips

- Run the installer to start the agent on boot.
- Right-click tray icon → "Exit" to stop.
- Use `.env` for dynamic config (port, printer, etc.)

---

## 📁 Folder Structure

```
printer_agent/
│
├── .env
├── README.md
├── build.bat
├── requirements.txt
├── printer_agent.iss
│
├── dist/                 
├── build/            
├── src/
│   ├── app.py
│   ├── tray.py
│   ├── printer_routes.py
│   ├── printer_utils.py
│   └── version.py
```

---
 