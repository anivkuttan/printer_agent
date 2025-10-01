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
        header += f"{store_name}\n".encode('utf-8')
    header += ESCPOSCommands.NORMAL_SIZE
    if location:
        header += f"📍\n{location}\n".encode('utf-8')
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
    receipt += f"Order No - مربطلا مقر:\n".encode('utf-8')
    receipt += ESCPOSCommands.BOLD_ON
    receipt += f"{receipt_data.get('order_no', '')}\n".encode('utf-8')
    receipt += ESCPOSCommands.BOLD_OFF
    receipt += create_separator_line()

    # Date and time info
    receipt += f"Order Date / تقولا خیرات : {receipt_data.get('order_date', '')}\n".encode(
        'utf-8')
    receipt += f"Order Time / تقولا تیقوت : {receipt_data.get('order_time', '')}\n".encode(
        'utf-8')
    receipt += f"cashier: {receipt_data.get('cashier', '')}\n".encode('utf-8')
    receipt += f"iron : {receipt_data.get('service_type', '')}\n".encode(
        'utf-8')
    receipt += create_separator_line()

    # Customer details section
    receipt += ESCPOSCommands.ALIGN_CENTER
    receipt += ESCPOSCommands.BOLD_ON
    receipt += "Customer Details\n".encode('utf-8')
    receipt += ESCPOSCommands.BOLD_OFF
    receipt += ESCPOSCommands.ALIGN_LEFT
    receipt += create_separator_line()

    customer = receipt_data.get('customer', {})
    receipt += f"{customer.get('username', '')} :  Customer\n".encode('utf-8')
    receipt += f"{customer.get('mobile', '')} :  Mobile No\n".encode('utf-8')
    receipt += f"{customer.get('area', '')} :  Area\n".encode('utf-8')
    receipt += f"{customer.get('street', '')} :  Street\n".encode('utf-8')
    receipt += f"{customer.get('block', '')} :  Block\n".encode('utf-8')
    receipt += f"{customer.get('floor', '')} :  Floor\n".encode('utf-8')
    receipt += f"{customer.get('building', '')} :  Building\n".encode('utf-8')

    receipt += create_separator_line()

    # Items header
    receipt += f"#{'':15}Item / مقر{'':8}ةکب/ {'':6}رعسلا /\n".encode('utf-8')
    receipt += create_separator_line()

    # Items list
    items = receipt_data.get('items', [])
    for i, item in enumerate(items, 1):
        name = item.get('name', '')
        quantity = item.get('quantity', 0)
        price = item.get('price', 0.0)

        # Format item line to match the receipt
        receipt += f"{i:<3}{name:<25}{quantity:<3}{price:.3f}\n".encode(
            'utf-8')

    receipt += create_separator_line()

    # Totals section
    total = receipt_data.get('total', 0.0)

    receipt += ESCPOSCommands.ALIGN_RIGHT
    receipt += f"Total / عومجم : {total:.3f} KWD\n".encode('utf-8')
    receipt += "\n".encode('utf-8')
    receipt += f"Total / عومجم\n".encode('utf-8')
    receipt += f"{total:.3f} KWD\n".encode('utf-8')
    receipt += "\n".encode('utf-8')
    receipt += f"Amount Received / ملتسم غلبم\n".encode('utf-8')
    receipt += f"{receipt_data.get('amount_received', 0.0):.3f} KWD\n".encode('utf-8')

    receipt += ESCPOSCommands.ALIGN_CENTER
    receipt += create_separator_line()

    # Footer with call number and timestamp
    receipt += f"Call {receipt_data.get('call_number', '')}\n".encode('utf-8')
    receipt += "\n".encode('utf-8')
    receipt += f"{receipt_data.get('timestamp', datetime.now().strftime('%d-%b-%Y %I:%M %p'))}\n".encode('utf-8')

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


# POS Receipt Printing Endpoint
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
            "message":  "Printer not found",

        }
        return jsonify(result), 404

    try:
        # Format receipt with ESC/POS commands
        formatted_receipt = format_laundry_receipt(receipt_data)

        # Clean and decode the receipt text
        receipt_text = formatted_receipt.decode('utf-8', errors='ignore')
        print(receipt_text)

        # Print to thermal printer
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
            "message":  "POS receipt printed successfully",

        }
        return jsonify(result)

    except Exception as e:
        result = {
            "statusCode": 500,
            "status": False,
            "message":  str(e),

        }
        return jsonify(result), 500
