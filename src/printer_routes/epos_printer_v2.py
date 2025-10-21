from datetime import datetime
import os
import subprocess
import sys
import threading
from flask import Blueprint, request, jsonify
import win32print
# import ESCPOSCommands
from .epos_comments import ESCPOSCommands
from src.utils.logger import logger
from src.utils.printer_utils import list_printers, get_default_printer, safe_base64_decode, safe_base64_decode_v2
import base64
import io
import re
from datetime import datetime
import uuid
import time
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pos_printer_v2_api = Blueprint("pos_printer_v2_api", __name__)

PRINTER_ENCODING = {
    'esc_code': b'\x1b\x74\x11',  # Default: CP720
    'encoding': 'cp720',
    'name': 'CP720'
}


def set_printer_encoding(encoding_number):
    """Set the printer encoding based on test results"""
    global PRINTER_ENCODING

    encodings = {
        1: {'esc_code': b'\x1b\x74\x11', 'encoding': 'cp720', 'name': 'CP720'},
        2: {'esc_code': b'\x1b\x74\x16', 'encoding': 'cp864', 'name': 'CP864'},
        3: {'esc_code': b'\x1b\x74\x28', 'encoding': 'cp1256', 'name': 'CP1256'},
        4: {'esc_code': b'\x1b\x74\x29', 'encoding': 'cp1256', 'name': 'CP1257'},
        5: {'esc_code': b'\x1b\x74\x07', 'encoding': 'iso-8859-6', 'name': 'ISO-8859-6'},
    }

    if encoding_number in encodings:
        PRINTER_ENCODING = encodings[encoding_number]
        print(f"Printer encoding set to: {PRINTER_ENCODING['name']}")
        return True
    return False


def encode_mixed_text(text):
    """Encode text with mixed English and Arabic characters"""
    result = b''
    parts = re.split(
        r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+)', text)

    for part in parts:
        if not part:
            continue

        if re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', part):
            result += PRINTER_ENCODING['esc_code']
            result += part.encode(PRINTER_ENCODING['encoding'],
                                  errors='ignore')
            result += b'\x1b\x74\x00'
        else:
            result += part.encode('utf-8', errors='ignore')

    return result


def decode_mixed_text(encoded_bytes):
    """Decode mixed encoded text for display/debugging"""
    result = ''
    i = 0
    current_encoding = 'utf-8'

    while i < len(encoded_bytes):
        if i + 2 < len(encoded_bytes) and encoded_bytes[i:i+2] == b'\x1b\x74':
            code_page = encoded_bytes[i+2]

            if code_page == 0x11:
                current_encoding = 'cp720'
            elif code_page == 0x16:
                current_encoding = 'cp864'
            elif code_page == 0x28:
                current_encoding = 'cp1256'
            elif code_page == 0x07:
                current_encoding = 'iso-8859-6'
            elif code_page == 0x00:
                current_encoding = 'utf-8'

            i += 3
            continue

        if i < len(encoded_bytes) and encoded_bytes[i] == 0x1b:
            if i + 1 < len(encoded_bytes):
                if encoded_bytes[i+1] in [0x61, 0x45, 0x2d]:
                    i += 3
                    continue
                else:
                    i += 2
                    continue
            else:
                i += 1
                continue

        try:
            if current_encoding in ['cp720', 'cp864', 'cp1256', 'iso-8859-6']:
                char = encoded_bytes[i:i +
                                     1].decode(current_encoding, errors='replace')
                result += char
                i += 1
            else:
                decoded = False
                for byte_count in range(1, 5):
                    if i + byte_count <= len(encoded_bytes):
                        try:
                            char = encoded_bytes[i:i +
                                                 byte_count].decode('utf-8')
                            result += char
                            i += byte_count
                            decoded = True
                            break
                        except UnicodeDecodeError:
                            continue
                if not decoded:
                    i += 1
        except Exception:
            i += 1

    return result


def create_separator_line():
    """Create a separator line"""
    return ESCPOSCommands.HORIZONTAL_LINE.encode('utf-8')


def create_laundry_receipt_header(store_name="", location=""):
    """Create receipt header with store info"""
    header = ESCPOSCommands.CODEPAGE_UTF8
    header += ESCPOSCommands.ALIGN_CENTER
    header += ESCPOSCommands.BOLD_ON
    header += ESCPOSCommands.DOUBLE_SIZE
    if store_name:
        header += encode_mixed_text(f"{store_name}\n")
    header += ESCPOSCommands.NORMAL_SIZE
    if location:
        header += encode_mixed_text(f"\n{location}\n")
    header += ESCPOSCommands.BOLD_OFF
    header += ESCPOSCommands.ALIGN_LEFT
    header += create_separator_line()
    return header


def format_laundry_receipt(data):
    """Format laundry service data into ESC/POS receipt format"""
    # Ensure data is a dictionary
    if not isinstance(data, dict):
        raise ValueError("Receipt data must be a dictionary")

    receipt_data = data

    # Start building receipt
    store_info = receipt_data.get('store', {})
    receipt = create_laundry_receipt_header(
        store_info.get('name', ''),
        store_info.get('location', '')
    )

    # Order details section
    receipt += ESCPOSCommands.ALIGN_LEFT
    receipt += encode_mixed_text(f"Order No - مربطلا مقر:\n")
    receipt += ESCPOSCommands.BOLD_ON
    receipt += encode_mixed_text(f"{receipt_data.get('order_no', '')}\n")
    receipt += ESCPOSCommands.BOLD_OFF
    receipt += create_separator_line()

    # Date and time info
    receipt += encode_mixed_text(
        f"Order Date / تقولا خیرات : {receipt_data.get('order_date', '')}\n")
    receipt += encode_mixed_text(
        f"Order Time / تقولا تیقوت : {receipt_data.get('order_time', '')}\n")
    receipt += encode_mixed_text(
        f"cashier: {receipt_data.get('cashier', '')}\n")
    receipt += encode_mixed_text(
        f"iron : {receipt_data.get('service_type', '')}\n")
    receipt += create_separator_line()

    # Customer details section
    receipt += ESCPOSCommands.ALIGN_CENTER
    receipt += ESCPOSCommands.BOLD_ON
    receipt += encode_mixed_text("Customer Details\n")
    receipt += ESCPOSCommands.BOLD_OFF
    receipt += ESCPOSCommands.ALIGN_LEFT
    receipt += create_separator_line()

    customer = receipt_data.get('customer', {})
    receipt += encode_mixed_text(
        f"{customer.get('username', '')} :  Customer\n")
    receipt += encode_mixed_text(
        f"{customer.get('mobile', '')} :  Mobile No\n")
    receipt += encode_mixed_text(f"{customer.get('area', '')} :  Area\n")
    receipt += encode_mixed_text(f"{customer.get('street', '')} :  Street\n")
    receipt += encode_mixed_text(f"{customer.get('block', '')} :  Block\n")
    receipt += encode_mixed_text(f"{customer.get('floor', '')} :  Floor\n")
    receipt += encode_mixed_text(
        f"{customer.get('building', '')} :  Building\n")

    receipt += create_separator_line()

    # Items header
    receipt += encode_mixed_text(
        f"#{'':15}Item / مقر{'':8}ةکب/ {'':6}رعسلا /\n")
    receipt += create_separator_line()

    # Items list
    items = receipt_data.get('items', [])
    for i, item in enumerate(items, 1):
        name = item.get('name', '')
        quantity = item.get('quantity', 0)
        price = item.get('price', 0.0)

        # Format item line to match the receipt
        receipt += encode_mixed_text(
            f"{i:<3}{name:<25}{quantity:<3}{price:.3f}\n")

    receipt += create_separator_line()

    # Totals section
    total = receipt_data.get('total', 0.0)

    receipt += ESCPOSCommands.ALIGN_RIGHT

    receipt += encode_mixed_text(f"Total / عومجم : {total:.3f} KWD\n")

    receipt += "\n".encode('utf-8')
    receipt += encode_mixed_text(f"Total / عومجم\n")
    receipt += encode_mixed_text(f"{total:.3f} KWD\n")
    receipt += "\n".encode('utf-8')
    receipt += f"Amount Received / ملتسم غلبم\n".encode('utf-8')
    receipt += encode_mixed_text(
        f"{receipt_data.get('amount_received', 0.0):.3f} KWD\n")

    receipt += ESCPOSCommands.ALIGN_CENTER
    receipt += create_separator_line()

    # Footer with call number and timestamp
    receipt += encode_mixed_text(
        f"Call {receipt_data.get('call_number', '')}\n")
    receipt += "\n".encode('utf-8')
    receipt += encode_mixed_text(
        f"{receipt_data.get('timestamp', datetime.now().strftime('%d-%b-%Y %I:%M %p'))}\n")

    # Cut paper
    receipt += ESCPOSCommands.CUT_PAPER

    return receipt


def convert_receipt_to_pdf(receipt_data):
    """
    Convert receipt data to a PDF that can be printed using your existing PDF printer
    Returns base64 encoded PDF string
    """

    # Generate the ESC/POS receipt first
    raw_receipt = format_laundry_receipt(receipt_data)

    # Clean and decode the receipt text
    receipt_text = raw_receipt.decode('utf-8', errors='ignore')

    # Remove ESC/POS control characters (they appear as weird characters)
    import re
    clean_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', receipt_text)

    # Create PDF in memory
    buffer = io.BytesIO()

    # Create PDF with receipt-like formatting
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(80*mm, 200*mm),  # Receipt-like narrow format
        rightMargin=5*mm,
        leftMargin=5*mm,
        topMargin=5*mm,
        bottomMargin=5*mm
    )

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles for receipt
    receipt_style = ParagraphStyle(
        'ReceiptStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
        spaceAfter=0,
        spaceBefore=0
    )

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=6,
        spaceBefore=0
    )

    center_style = ParagraphStyle(
        'CenterStyle',
        parent=receipt_style,
        alignment=TA_CENTER
    )

    right_style = ParagraphStyle(
        'RightStyle',
        parent=receipt_style,
        alignment=TA_RIGHT
    )

    # Build story (content)
    story = []
    lines = clean_text.split('\n')

    current_alignment = 'left'

    for line in lines:
        if not line.strip():
            story.append(Spacer(1, 3))
            continue

        # Detect alignment based on content
        if any(keyword in line.lower() for keyword in ['total', 'amount received', 'call']):
            if 'call' in line.lower():
                current_alignment = 'center'
            else:
                current_alignment = 'right'
        elif any(keyword in line for keyword in ['NewxLaundry', 'Ardiya', '📍']):
            current_alignment = 'center'
        elif line.strip().startswith('-'):
            current_alignment = 'left'

        # Choose style based on alignment
        if current_alignment == 'center':
            if any(keyword in line for keyword in ['NewxLaundry']):
                style = header_style
            else:
                style = center_style
        elif current_alignment == 'right':
            style = right_style
        else:
            style = receipt_style

        # Add line to story
        story.append(Paragraph(line.replace(' ', '&nbsp;'), style))

    # Build PDF
    doc.build(story)

    # Get PDF bytes and encode to base64
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return base64.b64encode(pdf_bytes).decode('utf-8')


def create_test_receipt_endpoint(receipt_data, printer_name="Microsoft Print to PDF"):
    """
    Create a test receipt and return the payload for your existing PDF printer endpoint
    """

    # Convert receipt to PDF
    pdf_base64 = convert_receipt_to_pdf(receipt_data)

    # Return the payload that matches your existing endpoint format
    return {
        "printer_name": printer_name,
        "pdf_data": pdf_base64
    }


def print_pdf(data: str, printer_name: str):
    """Print PDF document to specified printer"""
    # data = request.get_json()
    if not data:
        result = {
            "statusCode": 400,
            "status": False,
            "message": "Missing request data",

        }
        return jsonify(result), 400

    # printer_name = printer_name
    pdf_data = data  # Base64 encoded PDF

    if not printer_name or not pdf_data:
        result = {
            "statusCode": 400,
            "status": False,
            "message": "Missing printer_name or pdf_data",

        }
        return jsonify(result), 400

    try:
        # Set printer as default
        win32print.SetDefaultPrinter(printer_name)
    except Exception:
        result = {
            "statusCode": 404,
            "status": False,
            "message": "Printer not found",

        }
        return jsonify(result), 404

    try:
        # Create temporary PDF file
        cache_dir = os.path.join(os.environ.get(
            "TEMP", "C:\\Temp"), "print_jobs")
        os.makedirs(cache_dir, exist_ok=True)
        filename = f"pdf_print_{uuid.uuid4().hex}.pdf"
        tmp_path = os.path.join(cache_dir, filename)

        # Decode and write PDF
        pdf_bytes = safe_base64_decode_v2(pdf_data['pdf_data'])
        with open(tmp_path, "wb") as f:
            f.write(pdf_bytes)
            f.flush()
            os.fsync(f.fileno())

        # Verify file creation
        time.sleep(1)
        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) < 100:
            raise Exception(f"PDF file was not properly created: {tmp_path}")

        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))

    # Build absolute path to SumatraPDF.exe
        sumatra_path = os.path.join(
            base_path, "tools", "SumatraPDF", "SumatraPDF.exe")
        sumatra_path = os.path.abspath(sumatra_path)

        if not os.path.exists(sumatra_path):
            result = {
                "statusCode": 500,
                "status": False,
                "message": f"SumatraPDF not found at {sumatra_path}",

            }
            return jsonify(result), 500

        cmd = f'"{sumatra_path}" -print-to "{printer_name}" "{tmp_path}"'
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(cmd, shell=True, creationflags=CREATE_NO_WINDOW)

        # Schedule cleanup
        threading.Thread(target=delayed_cleanup, args=(
            tmp_path,), daemon=True).start()

        result = {
            "statusCode": 400,
            "status": False,
            "message": "PDF sent to printer successfully",

        }
        return jsonify(result)

    except Exception as e:
        result = {
            "statusCode": 500,
            "status": False,
            "message": str(e),

        }
        return jsonify(result), 500


def delayed_cleanup(path):
    """Delete temporary file after delay"""
    time.sleep(5)
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass


@pos_printer_v2_api.route("/test-receipt-v2", methods=["POST"])
def test_receipt():
    """Test receipt formatting by converting to PDF"""
    data = request.get_json()
    printer_name = data.get("printer_name")
    pdf_data = data.get("pdf_data")

    try:
        # Convert receipt data to PDF payload
        print_payload = create_test_receipt_endpoint(
            pdf_data, printer_name)

        # Use your existing PDF printing logic
        return print_pdf(print_payload, printer_name)

    except Exception as e:
        return jsonify({"status": 500, "error": True, "error_msg": str(e)}), 500


set_printer_encoding(1)


@pos_printer_v2_api.route("/print-pos-v2", methods=["POST"])
def print_pos():
    """Print POS receipt with ESC/POS formatting to thermal printer"""
    data = request.get_json()
    if not data:
        result = {
            "statusCode": 400,
            "status": False,
            "message": "Missing request data",
        }
        return jsonify(result), 400

    printer_name = data.get("printer_name")
    receipt_data = data.get("receipt_data")
    loop_turn = data.get("loop_turn", 1)

    if not printer_name or not receipt_data:
        result = {
            "statusCode": 400,
            "status": False,
            "message": "Missing printer_name or receipt_data",
        }
        return jsonify(result), 400

    try:
        # Set printer as default
        win32print.SetDefaultPrinter(printer_name)
    except Exception:
        result = {
            "statusCode": 404,
            "status": False,
            "message": "Printer not found",
        }
        return jsonify(result), 404

    try:
        # Format receipt with ESC/POS commands
        formatted_receipt = format_laundry_receipt(receipt_data)

        receipt_text = decode_mixed_text(formatted_receipt)
        print(f"Printing {loop_turn} time(s)...")
        print(receipt_text)

        # Print to thermal printer multiple times
        for i in range(loop_turn):
            hPrinter = win32print.OpenPrinter(printer_name)
            doc_info = ("POS Receipt", None, "RAW")
            hJob = win32print.StartDocPrinter(hPrinter, 1, doc_info)

            win32print.StartPagePrinter(hPrinter)
            win32print.WritePrinter(hPrinter, formatted_receipt)
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
            win32print.ClosePrinter(hPrinter)

        result = {
            "statusCode": 200,
            "status": True,
            "message": f"POS receipt printed {loop_turn} time(s) successfully",
        }
        return jsonify(result)

    except Exception as e:
        result = {
            "statusCode": 500,
            "status": False,
            "message": str(e),
        }
        return jsonify(result), 500


@pos_printer_v2_api.route("/test-arabic-encodings", methods=["POST"])
def test_arabic_encodings():
    """Test all Arabic encodings to find which works with your printer"""
    data = request.get_json()
    if not data:
        return jsonify({
            "statusCode": 400,
            "status": False,
            "message": "Missing request data"
        }), 400

    printer_name = data.get("printer_name")

    if not printer_name:
        return jsonify({
            "statusCode": 400,
            "status": False,
            "message": "Missing printer_name"
        }), 400

    try:
        win32print.SetDefaultPrinter(printer_name)
    except Exception:
        return jsonify({
            "statusCode": 404,
            "status": False,
            "message": "Printer not found"
        }), 404

    # Test Arabic text
    test_arabic = "مرحبا بك"  # "Welcome" in Arabic
    test_text = "Hello / مرحبا"

    # All common Arabic code pages for thermal printers
    code_pages = [
        {"name": "CP720 (Arabic - Transparent ASMO)",
         "esc_code": b'\x1b\x74\x11', "encoding": "cp720"},
        {"name": "CP864 (Arabic - IBM)",
         "esc_code": b'\x1b\x74\x16', "encoding": "cp864"},
        {"name": "CP1256 (Windows Arabic)",
         "esc_code": b'\x1b\x74\x28', "encoding": "cp1256"},
        {"name": "CP1257 (Windows Baltic - sometimes used)",
         "esc_code": b'\x1b\x74\x29', "encoding": "cp1256"},
        {"name": "ISO-8859-6 (Arabic)", "esc_code": b'\x1b\x74\x07',
         "encoding": "iso-8859-6"},
    ]

    try:
        hPrinter = win32print.OpenPrinter(printer_name)
        doc_info = ("Arabic Encoding Test", None, "RAW")
        hJob = win32print.StartDocPrinter(hPrinter, 1, doc_info)
        win32print.StartPagePrinter(hPrinter)

        # Print header
        receipt = b'\x1b\x40'  # Initialize printer
        receipt += b'\x1b\x61\x01'  # Center align
        receipt += b'\x1b\x45\x01'  # Bold ON
        receipt += "ARABIC ENCODING TEST\n".encode('utf-8')
        receipt += b'\x1b\x45\x00'  # Bold OFF
        receipt += "EPSON TM-T20III\n".encode('utf-8')
        receipt += b'\x1b\x61\x00'  # Left align
        receipt += b'-' * 48 + b'\n'
        receipt += "Check which line shows Arabic correctly:\n".encode('utf-8')
        receipt += b'-' * 48 + b'\n\n'

        # Test each code page
        for i, cp in enumerate(code_pages, 1):
            try:
                # Print code page name
                receipt += b'\x1b\x45\x01'  # Bold ON
                receipt += f"[{i}] {cp['name']}\n".encode('utf-8')
                receipt += b'\x1b\x45\x00'  # Bold OFF

                # Set code page
                receipt += cp['esc_code']

                # Print test text with this encoding
                receipt += f"Test: {test_text}\n".encode(
                    cp['encoding'], errors='replace')
                receipt += f"Arabic: {test_arabic}\n".encode(
                    cp['encoding'], errors='replace')

                # Reset to default
                receipt += b'\x1b\x74\x00'

                receipt += b'-' * 48 + b'\n'

            except Exception as e:
                receipt += f"ERROR with {cp['name']}: {str(e)}\n".encode(
                    'utf-8', errors='ignore')
                receipt += b'-' * 48 + b'\n'

        # Print footer
        receipt += b'\n'
        receipt += b'\x1b\x61\x01'  # Center align
        receipt += "Find the line with correct Arabic\n".encode('utf-8')
        receipt += "and use that encoding number!\n".encode('utf-8')
        receipt += b'\x1b\x61\x00'  # Left align
        receipt += b'\n\n\n\n'

        # Cut paper
        receipt += b'\x1d\x56\x00'

        # Send to printer
        win32print.WritePrinter(hPrinter, receipt)
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
        win32print.ClosePrinter(hPrinter)

        return jsonify({
            "statusCode": 200,
            "status": True,
            "message": "Test printed! Check which encoding shows Arabic correctly.",
            "encodings_tested": [cp['name'] for cp in code_pages],
        })

    except Exception as e:
        return jsonify({
            "statusCode": 500,
            "status": False,
            "message": f"Print error: {str(e)}"
        }), 500
