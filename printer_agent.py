# printer_agent.py

import base64
import os
import time
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
import win32print
import win32api
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

app = Flask(__name__)
CORS(app)

# --- Flask Agent Endpoints ---

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "version": "1.0"}), 200

@app.route("/printers", methods=["POST"])
def print_handler():
    data = request.get_json()
    if not data:
        return jsonify({"status": 400, "error": True, "error_msg": "Missing request data"}), 400

    printer_name = data.get("printer_name")
    printer_data = data.get("printer_data")
    data_type = data.get("data_type", "pdf")

    if not printer_name or not printer_data:
        return jsonify({"status": 400, "error": True, "error_msg": "Missing printer_name or printer_data"}), 400

    try:
        win32print.SetDefaultPrinter(printer_name)
    except Exception:
        return jsonify({"status": 404, "error": True, "error_msg": "Printer not found"}), 404

    try:
        time_val = int(time.time())

        if data_type == "pdf":
            pdf_bytes = base64.b64decode(printer_data)
            filename = f"{time_val}.pdf"
            with open(filename, "wb") as f:
                f.write(pdf_bytes)
            win32api.ShellExecute(0, "print", filename, f'/d:"{printer_name}"', ".", 0)
            return jsonify({"status": 200, "error": False, "message": "PDF sent to printer"})

        elif data_type == "terminal":
            hPrinter = win32print.OpenPrinter(printer_name)
            hJob = win32print.StartDocPrinter(hPrinter, 1, ("Terminal Print Job", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)
            win32print.WritePrinter(hPrinter, printer_data.encode("utf-8"))
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
            win32print.ClosePrinter(hPrinter)
            return jsonify({"status": 200, "error": False, "message": "Terminal text printed"})

        else:
            return jsonify({"status": 400, "error": True, "error_msg": "Unsupported data_type"}), 400

    except Exception as e:
        return jsonify({"status": 500, "error": True, "error_msg": str(e)}), 500

# --- System Tray Icon (Optional UI) ---
def create_tray_image():
    image = Image.new('RGB', (64, 64), color=(76, 175, 80))
    draw = ImageDraw.Draw(image)
    draw.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
    return image

def start_tray():
    icon = Icon("POS Agent", icon=create_tray_image(), menu=Menu(MenuItem("Exit", lambda icon, item: icon.stop())))
    icon.run()

# --- Start Flask Server + Tray Icon ---
if __name__ == "__main__":
    threading.Thread(target=start_tray, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
