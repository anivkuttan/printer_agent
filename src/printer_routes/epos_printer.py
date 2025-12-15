
# import sys
# from flask import Blueprint, request, jsonify
# import os
# import uuid
# import time
# import subprocess
# import threading
# import pdfkit
# import win32print
# from .epos_comments import ESCPOSCommands
# from src.utils.logger import logger
# from src.utils.printer_utils import list_printers, get_default_printer, safe_base64_decode

# pos_printer_api = Blueprint("new_printer_api", __name__)


# def format_receipt_line(left_text, right_text, total_width=48):
#     """Format a line with left and right aligned text"""
#     if len(left_text) + len(right_text) >= total_width:
#         return f"{left_text}\n{right_text.rjust(total_width)}\n"

#     spaces = total_width - len(left_text) - len(right_text)
#     return f"{left_text}{' ' * spaces}{right_text}\n"


# def create_receipt_header(store_name, address="", phone=""):
#     """Create a formatted receipt header"""
#     receipt = ESCPOSCommands.INIT
#     receipt += ESCPOSCommands.CODEPAGE_UTF8
#     receipt += ESCPOSCommands.ALIGN_CENTER
#     receipt += ESCPOSCommands.DOUBLE_SIZE
#     receipt += ESCPOSCommands.BOLD_ON
#     receipt += store_name.encode('utf-8') + b'\n'
#     receipt += ESCPOSCommands.NORMAL_SIZE
#     receipt += ESCPOSCommands.BOLD_OFF

#     if address:
#         receipt += address.encode('utf-8') + b'\n'
#     if phone:
#         receipt += phone.encode('utf-8') + b'\n'

#     receipt += ESCPOSCommands.ALIGN_LEFT
#     receipt += ESCPOSCommands.DOUBLE_LINE.encode('utf-8')

#     return receipt


# def create_receipt_footer(total_amount, payment_method="CASH", change=0):
#     """Create a formatted receipt footer"""
#     receipt = ESCPOSCommands.HORIZONTAL_LINE.encode('utf-8')
#     receipt += ESCPOSCommands.BOLD_ON
#     receipt += ESCPOSCommands.DOUBLE_HEIGHT
#     receipt += format_receipt_line("TOTAL:",
#                                    f"${total_amount:.2f}").encode('utf-8')
#     receipt += ESCPOSCommands.NORMAL_SIZE
#     receipt += ESCPOSCommands.BOLD_OFF

#     receipt += format_receipt_line("Payment:", payment_method).encode('utf-8')
#     if change > 0:
#         receipt += format_receipt_line("Change:",
#                                        f"${change:.2f}").encode('utf-8')

#     receipt += b'\n'
#     receipt += ESCPOSCommands.ALIGN_CENTER
#     receipt += "Thank you for your business!".encode('utf-8') + b'\n'
#     receipt += "Visit us again soon!".encode('utf-8') + b'\n'
#     receipt += ESCPOSCommands.FEED_LINES_3
#     receipt += ESCPOSCommands.CUT_PAPER

#     return receipt


# def format_pos_receipt(data):
#     """Format data into ESC/POS receipt format"""
#     if isinstance(data, str):
#         receipt = create_receipt_header("Your Store")
#         receipt += ESCPOSCommands.ALIGN_LEFT
#         receipt += data.encode('utf-8') + b'\n'
#         receipt += create_receipt_footer(0.00)
#         return receipt

#     elif isinstance(data, dict):
#         store_info = data.get('store', {})
#         items = data.get('items', [])
#         totals = data.get('totals', {})

#         # Header
#         receipt = create_receipt_header(
#             store_info.get('name', 'Store'),
#             store_info.get('address', ''),
#             store_info.get('phone', '')
#         )

#         # Date and receipt number
#         receipt += ESCPOSCommands.ALIGN_LEFT
#         receipt += f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n".encode('utf-8')
#         receipt += f"Receipt: {data.get('receipt_no', uuid.uuid4().hex[:8].upper())}\n".encode(
#             'utf-8')
#         receipt += ESCPOSCommands.HORIZONTAL_LINE.encode('utf-8')

#         # Items
#         for item in items:
#             name = item.get('name', 'Item')
#             qty = item.get('quantity', 1)
#             price = item.get('price', 0.00)
#             total = qty * price

#             receipt += f"{name}\n".encode('utf-8')
#             receipt += format_receipt_line(f"{qty} x ${price:.2f}",
#                                            f"${total:.2f}").encode('utf-8')

#         # Footer with totals
#         subtotal = totals.get('subtotal', 0.00)
#         tax = totals.get('tax', 0.00)
#         total = totals.get('total', subtotal + tax)
#         payment = totals.get('payment_method', 'CASH')
#         change = totals.get('change', 0.00)

#         if tax > 0:
#             receipt += ESCPOSCommands.HORIZONTAL_LINE.encode('utf-8')
#             receipt += format_receipt_line("Subtotal:",
#                                            f"${subtotal:.2f}").encode('utf-8')
#             receipt += format_receipt_line("Tax:",
#                                            f"${tax:.2f}").encode('utf-8')

#         receipt += create_receipt_footer(total, payment, change)
#         return receipt

#     else:
#         receipt = create_receipt_header("Receipt")
#         receipt += str(data).encode('utf-8') + b'\n'
#         receipt += create_receipt_footer(0.00)
#         return receipt


# def delayed_cleanup(path):
#     """Delete temporary file after delay"""
#     time.sleep(5)
#     try:
#         if os.path.exists(path):
#             os.remove(path)
#     except:
#         pass


# # Utility endpoint - Get available printers
# @pos_printer_api.route("/get-printers", methods=["GET"])
# def get_printers():
#     """Get list of available printers and default printer"""
#     try:
#         printer_names = list_printers()
#         default_printer = get_default_printer()
#         data = {
#             "statusCode": 200,
#             "status": True,
#             "message": "Agent is running",
#             "data": {"printers": printer_names,
#                      "default_printer": default_printer, }
#         }
#         return jsonify(data)
#     except Exception as e:
#         return jsonify({"statusCode": 500, "status": False, "message": str(e)}), 500


# # PDF Printing Endpoint
# @pos_printer_api.route("/print-pdf", methods=["POST"])
# def print_pdf():
#     """Print PDF document to specified printer"""
#     data = request.get_json()
#     if not data:
#         data = {
#             "statusCode": 400,
#             "status": False,
#             "message": "Missing request data",

#         }
#         return jsonify(data), 400

#     printer_name = data.get("printer_name")
#     pdf_data = data.get("pdf_data")  # Base64 encoded PDF

#     if not printer_name or not pdf_data:
#         data = {
#             "statusCode": 400,
#             "status": False,
#             "message": "Missing printer_name or pdf_data",

#         }
#         return jsonify(data), 400

#     try:
#         # Set printer as default
#         win32print.SetDefaultPrinter(printer_name)
#     except Exception:
#         data = {
#             "statusCode": 404,
#             "status": False,
#             "message": "Printer not found",

#         }
#         return jsonify(data), 404

#     try:
#         # Create temporary PDF file
#         cache_dir = os.path.join(os.environ.get(
#             "TEMP", "C:\\Temp"), "print_jobs")
#         os.makedirs(cache_dir, exist_ok=True)
#         filename = f"pdf_print_{uuid.uuid4().hex}.pdf"
#         tmp_path = os.path.join(cache_dir, filename)

#         # Decode and write PDF
#         pdf_bytes = safe_base64_decode(pdf_data)
#         with open(tmp_path, "wb") as f:
#             f.write(pdf_bytes)
#             f.flush()
#             os.fsync(f.fileno())

#         # Verify file creation
#         time.sleep(1)
#         if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) < 100:
#             raise Exception(f"PDF file was not properly created: {tmp_path}")

#         if getattr(sys, "frozen", False):
#             base_path = os.path.dirname(sys.executable)
#         else:
#             base_path = os.path.dirname(os.path.abspath(__file__))

#         sumatra_path = os.path.join(
#             base_path, "tools", "SumatraPDF", "SumatraPDF.exe")

#         sumatra_path = os.path.abspath(sumatra_path)

#         if not os.path.exists(sumatra_path):
#             data = {
#                 "statusCode": 500,
#                 "status": False,
#                 "message": f"SumatraPDF not found at {sumatra_path}",

#             }
#             return jsonify(data), 500

#         cmd = f'"{sumatra_path}" -print-to "{printer_name}" "{tmp_path}"'
#         CREATE_NO_WINDOW = 0x08000000
#         subprocess.Popen(cmd, shell=True, creationflags=CREATE_NO_WINDOW)

#         # Schedule cleanup
#         threading.Thread(target=delayed_cleanup, args=(
#             tmp_path,), daemon=True).start()
#         data = {
#             "statusCode": 200,
#             "status": True,
#             "message": "PDF sent to printer successfully",

#         }
#         return jsonify(data)

#     except Exception as e:
#         data = {
#             "statusCode": 500,
#             "status": False,
#             "message":  str(e),

#         }
#         return jsonify(data), 500


# # POS Receipt Printing Endpoint
# @pos_printer_api.route("/print-pos", methods=["POST"])
# def print_pos():
#     """Print POS receipt with ESC/POS formatting to thermal printer"""
#     data = request.get_json()
#     if not data:
#         return jsonify({"status": 400, "error": True, "error_msg": "Missing request data"}), 400

#     printer_name = data.get("printer_name")
#     receipt_data = data.get("receipt_data")

#     if not printer_name or not receipt_data:
#         return jsonify({"status": 400, "error": True, "error_msg": "Missing printer_name or receipt_data"}), 400

#     try:
#         # Set printer as default
#         win32print.SetDefaultPrinter(printer_name)
#     except Exception:
#         return jsonify({"status": 404, "error": True, "error_msg": "Printer not found"}), 404

#     try:
#         # Format receipt with ESC/POS commands
#         formatted_receipt = format_pos_receipt(receipt_data)

#         # Print to thermal printer
#         hPrinter = win32print.OpenPrinter(printer_name)
#         doc_info = ("POS Receipt", None, "RAW")
#         hJob = win32print.StartDocPrinter(hPrinter, 1, doc_info)

#         win32print.StartPagePrinter(hPrinter)
#         win32print.WritePrinter(hPrinter, formatted_receipt)
#         win32print.EndPagePrinter(hPrinter)
#         win32print.EndDocPrinter(hPrinter)
#         win32print.ClosePrinter(hPrinter)

#         return jsonify({"status": 200, "error": False, "message": "POS receipt printed successfully"})

#     except Exception as e:
#         return jsonify({"status": 500, "error": True, "error_msg": str(e)}), 500


# # Terminal/Plain Text Printing Endpoint
# @pos_printer_api.route("/print-terminal", methods=["POST"])
# def print_terminal():
#     """Print plain text to printer (no formatting)"""
#     data = request.get_json()
#     if not data:
#         return jsonify({"status": 400, "error": True, "error_msg": "Missing request data"}), 400

#     printer_name = data.get("printer_name")
#     text_data = data.get("text_data")

#     if not printer_name or not text_data:
#         return jsonify({"status": 400, "error": True, "error_msg": "Missing printer_name or text_data"}), 400

#     try:
#         # Set printer as default
#         win32print.SetDefaultPrinter(printer_name)
#     except Exception:
#         return jsonify({"status": 404, "error": True, "error_msg": "Printer not found"}), 404

#     try:
#         # Print plain text
#         hPrinter = win32print.OpenPrinter(printer_name)
#         doc_info = ("Terminal Print", None, "RAW")
#         hJob = win32print.StartDocPrinter(hPrinter, 1, doc_info)

#         win32print.StartPagePrinter(hPrinter)

#         # Convert string to bytes if necessary
#         if isinstance(text_data, str):
#             text_bytes = text_data.encode("utf-8")
#         else:
#             text_bytes = text_data

#         win32print.WritePrinter(hPrinter, text_bytes)
#         win32print.EndPagePrinter(hPrinter)
#         win32print.EndDocPrinter(hPrinter)
#         win32print.ClosePrinter(hPrinter)

#         return jsonify({"status": 200, "error": False, "message": "Terminal text printed successfully"})

#     except Exception as e:
#         return jsonify({"status": 500, "error": True, "error_msg": str(e)}), 500


# # HTML to PDF Printing Endpoint
# @pos_printer_api.route("/print-html", methods=["POST"])
# def print_html():
#     """Convert HTML to PDF and print"""

#     # Create cache directory for PDFs
#     cache_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "print_jobs")
#     os.makedirs(cache_dir, exist_ok=True)

#     # Generate unique filename
#     filename = f"html_print_{uuid.uuid4().hex}.pdf"
#     tmp_path = os.path.join(cache_dir, filename)

#     # Get request data
#     data = request.get_json()
#     if not data:
#         logger.warning("Missing request data in /print-html")
#         return jsonify({"status": 400, "error": True, "error_msg": "Missing request data"}), 400

#     printer_name = data.get("printer_name")
#     html_data = data.get("html_data")
#     paper_width = data.get("paper_width", "80mm")
#     paper_height = data.get("paper_height", "297mm")

#     if not printer_name or not html_data:
#         logger.warning(
#             f"Missing fields - printer_name: {printer_name}, html_data present: {bool(html_data)}")
#         return jsonify({"status": 400, "error": True, "error_msg": "Missing printer_name or html_data"}), 400

#     logger.info(
#         f"Print job started - Printer: {printer_name}, File: {filename}")

#     # Set printer as default
#     try:
#         win32print.SetDefaultPrinter(printer_name)
#     except Exception as e:
#         logger.error(f"Printer not found: {printer_name}, Error: {str(e)}")
#         return jsonify({"status": 404, "error": True, "error_msg": "Printer not found"}), 404

#     try:

#         if getattr(sys, "frozen", False):
#             base_path = os.path.dirname(sys.executable)
#         else:
#             base_path = os.path.dirname(os.path.abspath(__file__))

#         wkhtmltopdf_path = os.path.join(
#             base_path, "tools", "wkhtmltox", "bin", "wkhtmltopdf.exe")

#         if not os.path.exists(wkhtmltopdf_path):
#             logger.error(f"wkhtmltopdf not found at {wkhtmltopdf_path}")
#             return jsonify({"status": 500, "error": True, "error_msg": f"wkhtmltopdf not found at {wkhtmltopdf_path}"}), 500

#         config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
#         options = {
#             "page-width": paper_width,
#             "page-height": paper_height,
#             "encoding": "UTF-8",
#             "margin-top": "0.05in",
#             "margin-right": "0.05in",
#             "margin-bottom": "0.05in",
#             "margin-left": "0.05in",
#             "quiet": "",
#         }

#         pdfkit.from_string(html_data, tmp_path,
#                            configuration=config, options=options)

#         # Verify PDF creation
#         if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) < 100:
#             raise Exception(f"PDF file was not properly created: {tmp_path}")

#         logger.info(f"PDF created successfully at {tmp_path}")

#         sumatra_path = os.path.join(
#             base_path, "tools", "SumatraPDF", "SumatraPDF.exe")

#         if not os.path.exists(sumatra_path):
#             logger.error(f"SumatraPDF not found at {sumatra_path}")
#             return jsonify({"status": 500, "error": True, "error_msg": f"SumatraPDF not found at {sumatra_path}"}), 500

#         cmd = f'"{sumatra_path}" -print-to "{printer_name}" "{tmp_path}"'
#         CREATE_NO_WINDOW = 0x08000000
#         subprocess.Popen(cmd, shell=True, creationflags=CREATE_NO_WINDOW)

#         logger.info(
#             f"Print command sent to printer: {printer_name}, File: {tmp_path}")

#         # Schedule cleanup
#         threading.Thread(target=delayed_cleanup, args=(
#             tmp_path,), daemon=True).start()

#         return jsonify({"status": 200, "error": False, "message": "HTML converted to PDF and sent to printer successfully"})

#     except Exception as e:
#         logger.error(
#             f"Print job failed - Printer: {printer_name}, File: {tmp_path}, Error: {str(e)}", exc_info=True)
#         return jsonify({"status": 500, "error": True, "error_msg": str(e)}), 500
