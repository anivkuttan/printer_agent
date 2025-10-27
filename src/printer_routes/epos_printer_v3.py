from datetime import datetime
import os
import subprocess
import sys
import threading
import time
import uuid
import win32print
import win32api
import pdfkit
from flask import Blueprint, request, jsonify
 
pos_printer_v3_api = Blueprint("pos_printer_v3_api", __name__)


def generate_receipt_html(receipt_data):
    """Generate HTML receipt from receipt data"""

    store = receipt_data.get('store', {})
    customer = receipt_data.get('customer', {})
    items = receipt_data.get('items', [])

    # Build items HTML
    items_html = ""
    for i, item in enumerate(items, 1):
        name = item.get('name', '')
        quantity = item.get('quantity', 0)
        price = item.get('price', 0.0)
        items_html += f"""
        <tr>
            <td style="text-align: left;">{i}</td>
            <td style="text-align: left;">{name}</td>
            <td style="text-align: center;">{quantity}</td>
            <td style="text-align: right;">{price:.3f}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: 80mm 297mm;
                margin: 2mm;
            }}
            body {{
                font-family: 'Courier New', monospace;
                font-size: 11px;
                margin: 0;
                padding: 5px;
                direction: ltr;
            }}
            .center {{
                text-align: center;
            }}
            .bold {{
                font-weight: bold;
            }}
            .large {{
                font-size: 14px;
            }}
            .separator {{
                border-bottom: 1px dashed #000;
                margin: 5px 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            td {{
                padding: 2px 0;
            }}
            .right {{
                text-align: right;
            }}
            .arabic {{
                direction: rtl;
            }}
        </style>
    </head>
    <body>
        <!-- Header -->
        <div class="center bold large">
            {store.get('name', '')}
        </div>
        <div class="center">
            {store.get('location', '')}
        </div>
        <div class="separator"></div>

        <!-- Order Details -->
        <div>Order No - رقم الطلب:</div>
        <div class="bold">{receipt_data.get('order_no', '')}</div>
        <div class="separator"></div>

        <div>Order Date / تاريخ الوقت : {receipt_data.get('order_date', '')}</div>
        <div>Order Time / توقيت الوقت : {receipt_data.get('order_time', '')}</div>
        <div>cashier: {receipt_data.get('cashier', '')}</div>
        <div>iron : {receipt_data.get('service_type', '')}</div>
        <div class="separator"></div>

        <!-- Customer Details -->
        <div class="center bold">Customer Details</div>
        <div class="separator"></div>

        <div>{customer.get('username', '')} : Customer</div>
        <div>{customer.get('mobile', '')} : Mobile No</div>
        <div>{customer.get('area', '')} : Area</div>
        <div>{customer.get('street', '')} : Street</div>
        <div>{customer.get('block', '')} : Block</div>
        <div>{customer.get('floor', '')} : Floor</div>
        <div>{customer.get('building', '')} : Building</div>
        <div class="separator"></div>

        <!-- Items -->
        <table>
            <tr>
                <td style="width: 10%; text-align: left;">#</td>
                <td style="width: 50%; text-align: left;">Item / رقم</td>
                <td style="width: 15%; text-align: center;">Qty / كمية</td>
                <td style="width: 25%; text-align: right;">Price / السعر</td>
            </tr>
        </table>
        <div class="separator"></div>

        <table>
            {items_html}
        </table>
        <div class="separator"></div>

        <!-- Totals -->
        <div class="right">
            <div><strong>Total / مجموع : {receipt_data.get('total', 0.0):.3f} KWD</strong></div>
            <br>
            <div>Total / مجموع</div>
            <div>{receipt_data.get('total', 0.0):.3f} KWD</div>
            <br>
            <div>Amount Received / مبلغ مستلم</div>
            <div>{receipt_data.get('amount_received', 0.0):.3f} KWD</div>
        </div>
        <div class="separator"></div>

        <!-- Footer -->
        <div class="center">
            <div>Call {receipt_data.get('call_number', '')}</div>
            <br>
            <div>{receipt_data.get('timestamp', datetime.now().strftime('%d-%b-%Y %I:%M %p'))}</div>
        </div>

        <br><br>
    </body>
    </html>
    """

    return html


def print_html_to_pdf(html_content, printer_name, loop_turn=1, save_only=False):
    """Convert HTML to PDF and print using wkhtmltopdf"""

    # Set printer as default (skip if save_only mode)
    if not save_only:
        try:
            win32print.SetDefaultPrinter(printer_name)
        except Exception as e:
            raise Exception(f"Printer not found: {str(e)}")

    # wkhtmltopdf options
    options = {
        'page-width': 80,
        'page-height': 297,
        'encoding': "UTF-8",
        'custom-header': [('Accept-Encoding', 'gzip')],
        'no-outline': None,
        'margin-top': '0.05in',
        'margin-right': '0.05in',
        'margin-bottom': '0.05in',
        'margin-left': '0.05in',
    }

    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:

        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    wkhtmltopdf_path = os.path.join(
        base_path, "tools", "wkhtmltox", "bin", "wkhtmltopdf.exe")

    if not os.path.exists(wkhtmltopdf_path):
        raise Exception(f"wkhtmltopdf not found at: {wkhtmltopdf_path}")

    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

    pdf_files = []

    # Print multiple times if requested
    for i in range(loop_turn):
        # Generate unique filename
        ts = time.time()
        filename = f"receipt_{int(ts)}_{i}.pdf"

        # Convert HTML to PDF
        pdfkit.from_string(html_content, filename,
                           configuration=config, options=options)
        pdf_files.append(filename)

        # Print PDF (skip if save_only mode)
        if not save_only:
            win32api.ShellExecute(0, "print", filename,
                                  f'/d:"{printer_name}"', ".", 0)
            time.sleep(0.5)

    return pdf_files


@pos_printer_v3_api.route("/print-pos-v3", methods=["POST"])
def print_pos():
    """Print POS receipt using wkhtmltopdf"""
    data = request.get_json()

    if not data:
        return jsonify({
            "statusCode": 400,
            "status": False,
            "message": "Missing request data",
        }), 400

    printer_name = data.get("printer_name")
    receipt_data = data.get("receipt_data")
    loop_turn = data.get("loop_turn", 1)

    if not printer_name or not receipt_data:
        return jsonify({
            "statusCode": 400,
            "status": False,
            "message": "Missing printer_name or receipt_data",
        }), 400

    try:
        html_content = generate_receipt_html(receipt_data)

        print_html_to_pdf(html_content, printer_name, loop_turn)

        return jsonify({
            "statusCode": 200,
            "status": True,
            "message": f"POS receipt printed {loop_turn} time(s) successfully",
        })

    except Exception as e:
        return jsonify({
            "statusCode": 500,
            "status": False,
            "message": str(e),
        }), 500


@pos_printer_v3_api.route("/preview-receipt-v3", methods=["POST"])
def preview_receipt():
    """Preview receipt as PDF without printing - optionally print if requested"""
    data = request.get_json()

    if not data:
        return jsonify({
            "statusCode": 400,
            "status": False,
            "message": "Missing request data",
        }), 400

    receipt_data = data.get("receipt_data") or data.get("pdf_data")
    printer_name = data.get("printer_name")
    print_now = data.get("print_now", False)

    if not receipt_data:
        return jsonify({
            "statusCode": 400,
            "status": False,
            "message": "Missing receipt_data",
        }), 400

    try:
        # Generate HTML receipt
        html_content = generate_receipt_html(receipt_data)

        # wkhtmltopdf options
        options = {
            'page-width': 80,
            'page-height': 297,
            'encoding': "UTF-8",
            'no-outline': None,
            'margin-top': '0.05in',
            'margin-right': '0.05in',
            'margin-bottom': '0.05in',
            'margin-left': '0.05in',
        }

        # Locate wkhtmltopdf
        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))

        wkhtmltopdf_path = os.path.join(
            base_path, "tools", "wkhtmltox", "bin", "wkhtmltopdf.exe")

        if not os.path.exists(wkhtmltopdf_path):
            raise Exception(f"wkhtmltopdf not found at: {wkhtmltopdf_path}")

        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

        # 🔹 Create temporary directory (like older version)
        cache_dir = os.path.join(os.environ.get(
            "TEMP", "C:\\Temp"), "print_jobs")
        os.makedirs(cache_dir, exist_ok=True)

        # 🔹 Unique filename in TEMP folder
        preview_filename = f"receipt_preview_{uuid.uuid4().hex}.pdf"
        preview_path = os.path.join(cache_dir, preview_filename)

        # Generate PDF inside temp folder
        pdfkit.from_string(html_content, preview_path,
                           configuration=config, options=options)

        # Ensure file exists
        if not os.path.exists(preview_path) or os.path.getsize(preview_path) < 100:
            raise Exception(
                f"PDF file was not properly created: {preview_path}")

        # 🔹 If print_now is true, print using default printer
        if print_now:
            if not printer_name:
                raise Exception("Missing printer_name for printing")

            win32print.SetDefaultPrinter(printer_name)

            win32api.ShellExecute(
                0, "print", preview_path, f'/d:"{printer_name}"', ".", 0
            )

        return jsonify({
            "statusCode": 200,
            "status": True,
            "message": "Receipt preview generated successfully"
            + (" and sent to printer" if print_now else ""),
            "pdf_path": preview_path,
            "filename": preview_filename
        })

    except Exception as e:
        return jsonify({
            "statusCode": 500,
            "status": False,
            "message": str(e),
        }), 500

@pos_printer_v3_api.route("/preview-receipt-pdf-v3", methods=["POST"])
def preview_receipt_v3():
    """Preview receipt as PDF without printing - optionally print if requested"""
    data = request.get_json()

    if not data:
        return jsonify({
            "statusCode": 400,
            "status": False,
            "message": "Missing request data",
        }), 400

    receipt_data = data.get("receipt_data") or data.get("pdf_data")
    printer_name = data.get("printer_name")
    print_now = data.get("print_now", False)

    if not receipt_data:
        return jsonify({
            "statusCode": 400,
            "status": False,
            "message": "Missing receipt_data",
        }), 400

    try:
        # Generate HTML receipt
        html_content = generate_receipt_html(receipt_data)

        # wkhtmltopdf options
        options = {
            'page-width': '80mm',
            'encoding': "UTF-8",
            'no-outline': None,
            'margin-top': '0.05in',
            'margin-right': '0.05in',
            'margin-bottom': '0.05in',
            'margin-left': '0.05in',
        }

        # Locate wkhtmltopdf
        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))

        wkhtmltopdf_path = os.path.join(
            base_path, "tools", "wkhtmltox", "bin", "wkhtmltopdf.exe")

        if not os.path.exists(wkhtmltopdf_path):
            raise Exception(f"wkhtmltopdf not found at: {wkhtmltopdf_path}")

        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

        # Create temporary directory for PDFs
        cache_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "print_jobs")
        os.makedirs(cache_dir, exist_ok=True)

        preview_filename = f"receipt_preview_{uuid.uuid4().hex}.pdf"
        preview_path = os.path.join(cache_dir, preview_filename)

        # Generate PDF
        pdfkit.from_string(html_content, preview_path,
                           configuration=config, options=options)

        # Verify PDF
        if not os.path.exists(preview_path) or os.path.getsize(preview_path) < 100:
            raise Exception(f"PDF file was not properly created: {preview_path}")

        # ✅ Optional printing via SumatraPDF
        if print_now:
            if not printer_name:
                raise Exception("Missing printer_name for printing")

            # Validate printer
            printers = [p[2] for p in win32print.EnumPrinters(2)]
            if printer_name not in printers:
                raise Exception(f"Printer '{printer_name}' not found. Available: {printers}")

            # Locate SumatraPDF
            if getattr(sys, "frozen", False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            sumatra_path = os.path.join(base_path, "..","tools", "SumatraPDF", "SumatraPDF.exe")
            sumatra_path = os.path.abspath(sumatra_path)

            if not os.path.exists(sumatra_path):
                raise Exception(f"SumatraPDF not found at {sumatra_path}")

            # Print silently via SumatraPDF
            cmd = f'"{sumatra_path}" -print-to "{printer_name}" -silent "{preview_path}"'
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(cmd, shell=True, creationflags=CREATE_NO_WINDOW)

            # Optional cleanup thread
            threading.Thread(target=delayed_cleanup, args=(preview_path,), daemon=True).start()

        return jsonify({
            "statusCode": 200,
            "status": True,
            "message": "Receipt preview generated successfully"
                       + (" and sent to printer" if print_now else ""),
            "pdf_path": preview_path,
            "filename": preview_filename
        })

    except Exception as e:
        return jsonify({
            "statusCode": 500,
            "status": False,
            "message": str(e),
        }), 500

@pos_printer_v3_api.route("/test-arabic-encodings-v3", methods=["POST"])
def test_arabic_encodings():
    """Test which encodings your POS printer supports for Arabic text"""
    data = request.get_json()
    if not data:
        return jsonify({
            "status": False,
            "statusCode": 400,
            "message": "Missing request body (printer_name required)"
        }), 400

    printer_name = data.get("printer_name")
    if not printer_name:
        return jsonify({
            "status": False,
            "statusCode": 400,
            "message": "Missing printer_name"
        }), 400

    encodings_to_test = [
        "cp720", "cp864", "cp1256",
        "iso8859_6", "utf-8", "utf-16", "utf-32"
    ]

    arabic_sample = "مرحبا بالعالم"  # "Hello world" in Arabic
    results = {}

    try:
        win32print.SetDefaultPrinter(printer_name)
    except Exception as e:
        return jsonify({
            "status": False,
            "statusCode": 404,
            "message": f"Printer not found: {e}"
        }), 404

    for enc in encodings_to_test:
        try:
            encoded_text = arabic_sample.encode(enc, errors="replace")

            hPrinter = win32print.OpenPrinter(printer_name)
            doc_info = ("Arabic Encoding Test", None, "RAW")
            hJob = win32print.StartDocPrinter(hPrinter, 1, doc_info)

            win32print.StartPagePrinter(hPrinter)
            win32print.WritePrinter(
                hPrinter, f"--- Testing {enc} ---\n".encode("ascii"))
            win32print.WritePrinter(hPrinter, encoded_text + b"\n\n")
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
            win32print.ClosePrinter(hPrinter)

            results[enc] = "✅ Sent successfully"
        except Exception as e:
            results[enc] = f"❌ Error: {e}"

    return jsonify({
        "status": True,
        "statusCode": 200,
        "message": "Encoding test completed. Check printed output.",
        "results": results
    })


def delayed_cleanup(path):
    """Delete temporary file after delay"""
    time.sleep(5)
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass
