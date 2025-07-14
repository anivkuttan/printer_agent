import base64
import time
from flask import Blueprint, request, jsonify
import win32print
import win32api
from src.printer_utils import list_printers, get_default_printer, set_default_printer
from src.version import __version__

printer_api = Blueprint("printer_api", __name__)

@printer_api.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "version": __version__}), 200

@printer_api.route("/version", methods=["GET"])
def get_version():
    return jsonify({"version": __version__})

@printer_api.route("/get-printers", methods=["GET"])
def get_printers():
    try:
        printer_names = list_printers()
        default_printer = get_default_printer()
        return jsonify({
            "status": 200,
            "printers": printer_names,
            "default_printer": default_printer
        })
    except Exception as e:
        return jsonify({"status": 500, "error": True, "error_msg": str(e)}), 500

import os
import time
import base64
import tempfile
import win32api
import win32print
from flask import request, jsonify

@printer_api.route("/printers", methods=["POST"])
def print_handler():
    data = request.get_json()
    if not data:
        # logger.warning("Missing request data")
        return jsonify({
            "status": 400,
            "error": True,
            "error_msg": "Missing request data"
        }), 400

    printer_name = data.get("printer_name")
    printer_data = data.get("printer_data")
    data_type = data.get("data_type", "pdf")

    if not printer_name or not printer_data:
        # logger.warning("Missing printer_name or printer_data")
        return jsonify({
            "status": 400,
            "error": True,
            "error_msg": "Missing printer_name or printer_data"
        }), 400

    try:
        set_default_printer(printer_name)
    except Exception as e:
        # logger.error(f"Printer not found: {printer_name}")
        # send_webhook_log("ERROR", f"Printer not found: {printer_name}", e)
        return jsonify({
            "status": 404,
            "error": True,
            "error_msg": "Printer not found"
        }), 404

    try:
        time_val = int(time.time())

        if data_type == "pdf":
            pdf_bytes = base64.b64decode(printer_data)
            filename = os.path.join(tempfile.gettempdir(), f"{time_val}.pdf")
            with open(filename, "wb") as f:
                f.write(pdf_bytes)

            # logger.info(f"PDF written to: {filename}")
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

            # logger.info(f"Terminal text printed to: {printer_name}")
            return jsonify({"status": 200, "error": False, "message": "Terminal text printed"})

        else:
            # logger.warning(f"Unsupported data_type: {data_type}")
            return jsonify({
                "status": 400,
                "error": True,
                "error_msg": "Unsupported data_type"
            }), 400

    except Exception as e:
        # logger.exception("Unexpected error during print process")
        # send_webhook_log("ERROR", "Unexpected error during print process", e)
        return jsonify({"status": 500, "error": True, "error_msg": str(e)}), 500

