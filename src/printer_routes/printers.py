from flask import Blueprint, request, jsonify
import os
import uuid
import time
import subprocess
import threading
import pdfkit
import win32print
from src.utils.printer_utils import list_printers, get_default_printer, safe_base64_decode

printer_api = Blueprint("printer_api", __name__)


# @printer_api.route("/get-printers", methods=["GET"])
# def get_printers():
#     try:
#         printer_names = list_printers()
#         default_printer = get_default_printer()
#         return jsonify({
#             "status": 200,
#             "printers": printer_names,
#             "default_printer": default_printer,
#         })
#     except Exception as e:
#         return jsonify({"status": 500, "error": True, "error_msg": str(e)}), 500


@printer_api.route("/printers", methods=["POST"])
def print_handler():
    data = request.get_json()
    if not data:
        return jsonify({"status": 400, "error": True, "error_msg": "Missing request data"}), 400

    printer_name = data.get("printer_name")
    printer_data = data.get("printer_data")
    data_type = data.get("data_type", "pdf")  # terminal

    if not printer_name or not printer_data:
        return jsonify({"status": 400, "error": True, "error_msg": "Missing printer_name or printer_data"}), 400

    try:
        win32print.SetDefaultPrinter(printer_name)
    except Exception:
        return jsonify({"status": 404, "error": True, "error_msg": "Printer not found"}), 404

    try:
        if data_type == "terminal":  # pdf
            hPrinter = win32print.OpenPrinter(printer_name)
            doc_info = ("Terminal Print Job", None, "RAW")
            hJob = win32print.StartDocPrinter(hPrinter, 1, doc_info)

            win32print.StartPagePrinter(hPrinter)
            win32print.WritePrinter(hPrinter, printer_data.encode("utf-8"))
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
            win32print.ClosePrinter(hPrinter)

            return jsonify({"status": 200, "error": False, "message": "Terminal text sent to printer"})

        # Create PDF path
        cache_dir = os.path.join(os.environ.get(
            "TEMP", "C:\\Temp"), "print_jobs")
        os.makedirs(cache_dir, exist_ok=True)
        filename = f"print_{uuid.uuid4().hex}.pdf"
        tmp_path = os.path.join(cache_dir, filename)

        if data_type == "pdf":
            pdf_bytes = safe_base64_decode(printer_data)
            with open(tmp_path, "wb") as f:
                f.write(pdf_bytes)
                f.flush()
                os.fsync(f.fileno())

        elif data_type == "html":
            current_dir = os.path.dirname(os.path.abspath(__file__))
            wkhtmltopdf_path = os.path.join(
                current_dir, "..", "tools", "wkhtmltox", "bin", "wkhtmltopdf.exe")

            wkhtmltopdf_path = os.path.abspath(wkhtmltopdf_path)
            if not os.path.exists(wkhtmltopdf_path):
                return jsonify({"status": 500, "error": True, "error_msg": f"wkhtmltopdf not found at {wkhtmltopdf_path}"}), 500

            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
            options = {
                "page-width": "80mm",
                "page-height": "297mm",
                "encoding": "UTF-8",
                "margin-top": "0.05in",
                "margin-right": "0.05in",
                "margin-bottom": "0.05in",
                "margin-left": "0.05in",
                "quiet": "",
            }

            pdfkit.from_string(printer_data, tmp_path,
                               configuration=config, options=options)
        else:
            return jsonify({"status": 400, "error": True, "error_msg": f"Unsupported data_type: {data_type}"}), 400

        # Wait and verify
        time.sleep(2)
        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) < 100:
            raise Exception(f"PDF file was not properly created: {tmp_path}")

        # Print via Sumatra
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sumatra_path = os.path.join(
            current_dir, "..", "tools", "SumatraPDF", "SumatraPDF.exe")
        sumatra_path = os.path.abspath(sumatra_path)

        if not os.path.exists(sumatra_path):
            return jsonify({"status": 500, "error": True, "error_msg": f"SumatraPDF not found at {sumatra_path}"}), 500

        cmd = f'"{sumatra_path}" -print-to "{printer_name}" "{tmp_path}"'
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(cmd, shell=True, creationflags=CREATE_NO_WINDOW)

        # Cleanup
        def delayed_cleanup(path):
            time.sleep(5)
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass

        threading.Thread(target=delayed_cleanup, args=(
            tmp_path,), daemon=True).start()

        return jsonify({"status": 200, "error": False, "message": f"{data_type.upper()} content sent to printer"})

    except Exception as e:
        return jsonify({"status": 500, "error": True, "error_msg": str(e)}), 500
