import win32print 
import arabic_reshaper
from flask import Blueprint, request, jsonify
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

from src.utils.logger import logger

pos_printer_v6_api = Blueprint("pos_printer_v6_api", __name__)

# ESC/POS Commands
ESC_INIT = b'\x1B\x40'
ESC_ALIGN_CENTER = b'\x1B\x61\x01'
ESC_ALIGN_LEFT = b'\x1B\x61\x00'
ESC_ALIGN_RIGHT = b'\x1B\x61\x02'


def print_text_line(printer_name, text, font_size=30, align='left', bold=False):
    """Print a single line of text (English only)"""
    try:
        font = None
        font_options = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf",
        ]
        
        for font_path in font_options:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        width = 576
        temp_img = Image.new('1', (width, 100), 1)
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        padding = 10
        img_height = text_height + (2 * padding)
        image = Image.new('1', (width, img_height), 1)
        draw = ImageDraw.Draw(image)
        
        if align == 'center':
            x = (width - text_width) // 2
        elif align == 'right':
            x = width - text_width - padding
        else:
            x = padding
        
        y = padding
        draw.text((x, y), text, font=font, fill=0)
        
        if width % 8 != 0:
            new_width = ((width // 8) + 1) * 8
            new_image = Image.new('1', (new_width, img_height), 1)
            new_image.paste(image, (0, 0))
            image = new_image
            width = new_width
        
        img_bytes = []
        for y in range(img_height):
            for x in range(0, width, 8):
                byte_val = 0
                for bit in range(8):
                    pixel = image.getpixel((x + bit, y))
                    if pixel == 0:
                        byte_val |= (1 << (7 - bit))
                img_bytes.append(byte_val)
        
        return bytes(img_bytes), width, img_height
    except Exception as e:
        return None, 0, 0


def print_bilingual_field(english_text, arabic_text="", font_size=25, align='center'):
    """Generate bitmap for bilingual field - Arabic first, then English"""
    try:
        if arabic_text:
            reshaped = arabic_reshaper.reshape(arabic_text)
            bidi_text = get_display(reshaped)
            # Arabic first for Kuwait
            combined_text = f"{bidi_text} / {english_text}"
        else:
            combined_text = english_text
        
        font = None
        font_options = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf",
        ]
        
        for font_path in font_options:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        width = 576
        temp_img = Image.new('1', (width, 100), 1)
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), combined_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        padding = 5
        img_height = text_height + (2 * padding)
        image = Image.new('1', (width, img_height), 1)
        draw = ImageDraw.Draw(image)
        
        # Center or left align
        if align == 'center':
            x = (width - text_width) // 2
        else:
            x = padding
        y = padding
        
        draw.text((x, y), combined_text, font=font, fill=0)
        
        if width % 8 != 0:
            new_width = ((width // 8) + 1) * 8
            new_image = Image.new('1', (new_width, img_height), 1)
            new_image.paste(image, (0, 0))
            image = new_image
            width = new_width
        
        img_bytes = []
        for y in range(img_height):
            for x in range(0, width, 8):
                byte_val = 0
                for bit in range(8):
                    pixel = image.getpixel((x + bit, y))
                    if pixel == 0:
                        byte_val |= (1 << (7 - bit))
                img_bytes.append(byte_val)
        
        return bytes(img_bytes), width, img_height
    except Exception as e:
        return None, 0, 0


def print_item_line(item_num, english_text, arabic_text, qty, amount, font_size=18):
    """Generate bitmap for item - number + name on line 1, arabic on line 2, qty and amount on right"""
    try:
        reshaped = arabic_reshaper.reshape(arabic_text)
        bidi_text = get_display(reshaped)
        
        font = None
        font_options = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf",
        ]
        
        for font_path in font_options:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        width = 576
        padding = 8
        line_spacing = 4
        
        # Prepare texts - keep them simple
        num_text = f"{item_num}."
        
        # Limit name length
        if len(english_text) > 10:
            english_line = english_text[:10]
        else:
            english_line = english_text
        
        # Simple formatting
        qty_text = str(qty)
        amount_text = f"{amount:.2f}"  # Use 2 decimals to be safe
        
        # Measure text sizes
        temp_img = Image.new('1', (width, 100), 1)
        temp_draw = ImageDraw.Draw(temp_img)
        
        num_bbox = temp_draw.textbbox((0, 0), num_text, font=font)
        num_width = num_bbox[2] - num_bbox[0]
        
        english_bbox = temp_draw.textbbox((0, 0), english_line, font=font)
        line_height = english_bbox[3] - english_bbox[1]
        
        # Fixed positions approach - divide width into sections
        # Section 1: Item number and name (0-350)
        # Section 2: Qty (380-430)
        # Section 3: Amount (450-560)
        
        # Calculate total height
        img_height = (line_height * 2) + line_spacing + (2 * padding)
        
        # Create image
        image = Image.new('1', (width, img_height), 1)
        draw = ImageDraw.Draw(image)
        
        # Line 1
        y_pos = padding
        
        # Draw number and name on left
        x_pos = padding
        draw.text((x_pos, y_pos), num_text, font=font, fill=0)
        x_pos += num_width + 5
        draw.text((x_pos, y_pos), english_line, font=font, fill=0)
        
        # Draw qty at fixed position
        draw.text((380, y_pos), qty_text, font=font, fill=0)
        
        # Draw amount at fixed position
        draw.text((460, y_pos), amount_text, font=font, fill=0)
        
        # Line 2: Arabic name
        y_pos += line_height + line_spacing
        x_pos = padding + num_width + 5
        draw.text((x_pos, y_pos), bidi_text, font=font, fill=0)
        
        # Ensure width is multiple of 8
        if width % 8 != 0:
            new_width = ((width // 8) + 1) * 8
            new_image = Image.new('1', (new_width, img_height), 1)
            new_image.paste(image, (0, 0))
            image = new_image
            width = new_width
        
        img_bytes = []
        for y in range(img_height):
            for x in range(0, width, 8):
                byte_val = 0
                for bit in range(8):
                    pixel = image.getpixel((x + bit, y))
                    if pixel == 0:
                        byte_val |= (1 << (7 - bit))
                img_bytes.append(byte_val)
        
        return bytes(img_bytes), width, img_height
    except Exception as e:
        return None, 0, 0


def print_item_header(font_size=18):
    """Generate bitmap for item header with proper alignment"""
    try:
        font = None
        font_options = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf",
        ]
        
        for font_path in font_options:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        width = 576
        padding = 8
        
        # Header texts
        header1 = "#  Item"
        header2 = "Qty"
        header3 = "Amount"
        
        # Measure height
        temp_img = Image.new('1', (width, 100), 1)
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), header1, font=font)
        text_height = bbox[3] - bbox[1]
        
        img_height = text_height + (2 * padding)
        image = Image.new('1', (width, img_height), 1)
        draw = ImageDraw.Draw(image)
        
        y = padding
        
        # Draw headers at same positions as items
        draw.text((padding, y), header1, font=font, fill=0)
        draw.text((380, y), header2, font=font, fill=0)
        draw.text((460, y), header3, font=font, fill=0)
        
        if width % 8 != 0:
            new_width = ((width // 8) + 1) * 8
            new_image = Image.new('1', (new_width, img_height), 1)
            new_image.paste(image, (0, 0))
            image = new_image
            width = new_width
        
        img_bytes = []
        for y in range(img_height):
            for x in range(0, width, 8):
                byte_val = 0
                for bit in range(8):
                    pixel = image.getpixel((x + bit, y))
                    if pixel == 0:
                        byte_val |= (1 << (7 - bit))
                img_bytes.append(byte_val)
        
        return bytes(img_bytes), width, img_height
    except Exception as e:
        return None, 0, 0


def print_dashed_line(width=576):
    """Generate a dashed line bitmap"""
    img_height = 5
    image = Image.new('1', (width, img_height), 1)
    draw = ImageDraw.Draw(image)
    
    for x in range(0, width, 10):
        draw.line([(x, 2), (x+5, 2)], fill=0, width=1)
    
    if width % 8 != 0:
        new_width = ((width // 8) + 1) * 8
        new_image = Image.new('1', (new_width, img_height), 1)
        new_image.paste(image, (0, 0))
        image = new_image
        width = new_width
    
    img_bytes = []
    for y in range(img_height):
        for x in range(0, width, 8):
            byte_val = 0
            for bit in range(8):
                pixel = image.getpixel((x + bit, y))
                if pixel == 0:
                    byte_val |= (1 << (7 - bit))
            img_bytes.append(byte_val)
    
    return bytes(img_bytes), width, img_height


def send_bitmap(hPrinter, img_bytes, width, height):
    """Send bitmap data to printer"""
    width_bytes = width // 8
    xL = width_bytes & 0xFF
    xH = (width_bytes >> 8) & 0xFF
    yL = height & 0xFF
    yH = (height >> 8) & 0xFF
    
    cmd = bytes([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH])
    win32print.WritePrinter(hPrinter, cmd)
    win32print.WritePrinter(hPrinter, img_bytes)


def print_end_shift_line(label, value, font_size=22, arabic_label=""):
    """Generate bitmap for end-shift report line with label and value"""
    try:
        # If Arabic label provided and not empty, format bilingual
        if arabic_label:
            reshaped = arabic_reshaper.reshape(arabic_label)
            bidi_text = get_display(reshaped)
            display_label = f"{bidi_text} / {label}"
        else:
            display_label = label
        
        font = None
        font_options = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf",
        ]
        
        for font_path in font_options:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        width = 576
        padding = 10
        
        # Use conservative printable area - thermal printers often have ~5-8mm margins
        # At 203 DPI (common for 58mm thermal): 8mm ≈ 64 pixels per side
        # So safe printable width is around 448-480 pixels
        safe_margin = 48  # pixels from each edge
        printable_width = width - (safe_margin * 2)  # 480 pixels
        
        # Measure text using temp image
        temp_img = Image.new('1', (width, 100), 1)
        temp_draw = ImageDraw.Draw(temp_img)
        label_bbox = temp_draw.textbbox((0, 0), display_label, font=font)
        value_bbox = temp_draw.textbbox((0, 0), value, font=font)
        text_height = max(label_bbox[3] - label_bbox[1], value_bbox[3] - value_bbox[1])
        value_width = value_bbox[2] - value_bbox[0]
        
        img_height = text_height + (2 * padding)
        image = Image.new('1', (width, img_height), 1)
        draw = ImageDraw.Draw(image)
        
        y = padding
        
        # Draw label on left (with safe margin)
        draw.text((safe_margin, y), display_label, font=font, fill=0)
        
        # Draw value on right (within safe printable area)
        x_value = width - safe_margin - value_width
        draw.text((x_value, y), value, font=font, fill=0)
        
        # Ensure width is multiple of 8
        if width % 8 != 0:
            new_width = ((width // 8) + 1) * 8
            new_image = Image.new('1', (new_width, img_height), 1)
            new_image.paste(image, (0, 0))
            image = new_image
            width = new_width
        
        img_bytes = []
        for y in range(img_height):
            for x in range(0, width, 8):
                byte_val = 0
                for bit in range(8):
                    pixel = image.getpixel((x + bit, y))
                    if pixel == 0:
                        byte_val |= (1 << (7 - bit))
                img_bytes.append(byte_val)
        
        return bytes(img_bytes), width, img_height
    except Exception as e:
        return None, 0, 0


@pos_printer_v6_api.route("/print-receipt", methods=["POST"]) 
def print_receipt_route():
    from flask import request, jsonify

    try:
        data = request.get_json()
        print_receipt(data)

        return jsonify({
            "status": True,
            "message": "Print job executed"
        }), 200

    except ValueError as e:
        return jsonify({
            "status": False,
            "message": str(e)
        }), 400

    except Exception as e:
        logger.exception(e)
        return jsonify({
            "status": False,
            "message": "Internal server error"
        }), 500
        
def print_receipt(data,flask_mode=False):
    """Print a complete bilingual receipt"""
    
    if not data or not data.get("printer_name") or not data.get("receipt_data"):
        if flask_mode:
            from flask import jsonify
            return jsonify({
                "status": False,
                "statusCode": 400,
                "message": "Missing printer_name or receipt_data"
            }), 400
        else:
            logger.error("Missing printer_name or receipt_data")
            return   
 
        
    
    printer_name = data.get("printer_name")
    receipt = data.get("receipt_data")
    
    try:
        hPrinter = win32print.OpenPrinter(printer_name)
        doc_info = ("Receipt Print", None, "RAW")
        win32print.StartDocPrinter(hPrinter, 1, doc_info)
        win32print.StartPagePrinter(hPrinter)
        
        win32print.WritePrinter(hPrinter, ESC_INIT)
        
        # Store Name
        store_name = receipt.get("store", {}).get("name", "Store Name")
        img_bytes, w, h = print_text_line(printer_name, store_name, font_size=40, align='center')
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        # Store Location
        location = receipt.get("store", {}).get("location", "Location")
        img_bytes, w, h = print_text_line(printer_name, location, font_size=25, align='center')
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        img_bytes, w, h = print_dashed_line()
        send_bitmap(hPrinter, img_bytes, w, h)
        
        # Order details - CENTER ALIGNED
        order_no_ar = receipt.get('order_no_arabic', 'رقم الطلب')
        order_no_en = f"{receipt.get('order_no', 'N/A')} : Order No"
        img_bytes, w, h = print_bilingual_field(order_no_en, order_no_ar, font_size=23)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        order_date_ar = receipt.get('order_date_arabic', 'تاريخ الطلب')
        order_date_en = f"{receipt.get('order_date', 'N/A')} : Order Date"
        img_bytes, w, h = print_bilingual_field(order_date_en, order_date_ar, font_size=23)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        order_time_ar = receipt.get('order_time_arabic', 'وقت الطلب')
        order_time_en = f"{receipt.get('order_time', 'N/A')} : Order Time"
        img_bytes, w, h = print_bilingual_field(order_time_en, order_time_ar, font_size=23)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        cashier_ar = receipt.get('cashier_arabic', 'الكاشير')
        cashier_en = f"{receipt.get('cashier', 'N/A')} : Cashier"
        img_bytes, w, h = print_bilingual_field(cashier_en, cashier_ar, font_size=23)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        service_ar = receipt.get('service_type_arabic', 'الخدمة')
        service_en = f"{receipt.get('service_type', 'N/A')} : Service"
        img_bytes, w, h = print_bilingual_field(service_en, service_ar, font_size=23)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        img_bytes, w, h = print_dashed_line()
        send_bitmap(hPrinter, img_bytes, w, h)
        
        # Customer Details Header
        cust_header_en = "Customer Details"
        cust_header_ar = receipt.get('customer_details_arabic', 'تفاصيل العميل')
        img_bytes, w, h = print_text_line(printer_name, cust_header_en, font_size=28, align='center')
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        reshaped = arabic_reshaper.reshape(cust_header_ar)
        bidi_text = get_display(reshaped)
        img_bytes, w, h = print_text_line(printer_name, bidi_text, font_size=26, align='center')
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        img_bytes, w, h = print_dashed_line()
        send_bitmap(hPrinter, img_bytes, w, h)
        
        # Customer Info - FORMAT: value : label
        customer = receipt.get("customer", {})
        
        cust_name_ar = customer.get('username_arabic', 'العميل')
        cust_name_en = f"{customer.get('username', 'N/A')} : Customer"
        img_bytes, w, h = print_bilingual_field(cust_name_en, cust_name_ar, font_size=23)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        mobile_ar = customer.get('mobile_arabic', 'رقم الجوال')
        mobile_en = f"{customer.get('mobile', 'N/A')} : Mobile No"
        img_bytes, w, h = print_bilingual_field(mobile_en, mobile_ar, font_size=23)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        area_ar = customer.get('area_arabic', 'المنطقة')
        area_en = f"{customer.get('area', 'N/A')} : Area"
        img_bytes, w, h = print_bilingual_field(area_en, area_ar, font_size=23)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        street_ar = customer.get('street_arabic', 'الشارع')
        street_en = f"{customer.get('street', 'N/A')} : Street"
        img_bytes, w, h = print_bilingual_field(street_en, street_ar, font_size=23)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        block_ar = customer.get('block_arabic', 'القطعة')
        block_en = f"{customer.get('block', 'N/A')} : Block"
        img_bytes, w, h = print_bilingual_field(block_en, block_ar, font_size=23)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        floor_ar = customer.get('floor_arabic', 'الطابق')
        floor_en = f"{customer.get('floor', 'N/A')} : Floor"
        img_bytes, w, h = print_bilingual_field(floor_en, floor_ar, font_size=23)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        building_ar = customer.get('building_arabic', 'المبنى')
        building_en = f"{customer.get('building', 'N/A')} : Building"
        img_bytes, w, h = print_bilingual_field(building_en, building_ar, font_size=23)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        img_bytes, w, h = print_dashed_line()
        send_bitmap(hPrinter, img_bytes, w, h)
        
        # Items Header - use the new aligned header
        img_bytes, w, h = print_item_header(font_size=18)
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        img_bytes, w, h = print_dashed_line()
        send_bitmap(hPrinter, img_bytes, w, h)
        
        # Print items
        items = receipt.get("items", [])
        for idx, item in enumerate(items, 1):
            english_name = item.get("english", item.get("name", "Item"))
            arabic_name = item.get("arabic", "بند")
            qty = item.get("quantity", 1)
            price = item.get("price", 0.0)
            
            img_bytes, w, h = print_item_line(idx, english_name, arabic_name, qty, price, font_size=18)
            if img_bytes:
                send_bitmap(hPrinter, img_bytes, w, h)
        
        img_bytes, w, h = print_dashed_line()
        send_bitmap(hPrinter, img_bytes, w, h)
        
        # Total
        total = receipt.get("total", 0.0)
        total_line = f"Total: {total:.3f} KWD"
        img_bytes, w, h = print_text_line(printer_name, total_line, font_size=24, align='right')
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        win32print.WritePrinter(hPrinter, b"\n")
        
        # Amount Received
        amount_received = receipt.get("amount_received", 0.0)
        received_line = f"Received: {amount_received:.3f} KWD"
        img_bytes, w, h = print_text_line(printer_name, received_line, font_size=22, align='right')
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        # Call Number
        if receipt.get("call_number"):
            call_line = f"Call Number : {receipt.get('call_number')}"
            img_bytes, w, h = print_text_line(printer_name, call_line, font_size=23, align='left')
            if img_bytes:
                send_bitmap(hPrinter, img_bytes, w, h)
        
        win32print.WritePrinter(hPrinter, b"\n\n\n")
        
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
        win32print.ClosePrinter(hPrinter)
        msg = f"Receipt printed successfully on printer: {printer_name}"
        logger.info(msg)

        if flask_mode:
            from flask import jsonify
            return jsonify({"status": True, "statusCode": 200, "message": msg}), 200
        
        
        
    except Exception as e:
        logger.info(f"Print error: {e}")
        if flask_mode:
            from flask import jsonify
            return jsonify({"status": False, "statusCode": 500, "message": f"Print error: {str(e)}"}), 500
    

def print_bilingual_text(printer_name, english_text, arabic_text, font_size=35, align='left'):
    """
    Print English text followed by / and Arabic text on the same line.
    Example: "Shirt / قميص"
    
    Args:
        printer_name: Windows printer name
        english_text: English text
        arabic_text: Arabic text
        font_size: Font size (20-60 recommended)
        align: 'left', 'center', 'right'
    """
    try:
        # Reshape and reverse Arabic text
        reshaped = arabic_reshaper.reshape(arabic_text)
        bidi_text = get_display(reshaped, base_dir='R')
        
        # Load system font that supports Arabic
        font = None
        font_options = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "arial.ttf",
        ]
        
        for font_path in font_options:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        # Create combined text: "English / Arabic"
        combined_text = f"{english_text} / {bidi_text}"
        
        # Measure text dimensions
        width = 576  # Standard thermal printer width
        temp_img = Image.new('1', (width, 100), 1)
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), combined_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Create final image with padding
        padding = 10
        img_height = text_height + (2 * padding)
        image = Image.new('1', (width, img_height), 1)  # 1-bit B&W image
        draw = ImageDraw.Draw(image)
        
        # Position text based on alignment
        if align == 'center':
            x = (width - text_width) // 2
        elif align == 'right':
            x = width - text_width - padding
        else:  # left
            x = padding
        
        y = padding
        
        # Draw the combined text (black on white)
        draw.text((x, y), combined_text, font=font, fill=0)
        
        # Ensure width is multiple of 8 for bitmap printing
        if width % 8 != 0:
            new_width = ((width // 8) + 1) * 8
            new_image = Image.new('1', (new_width, img_height), 1)
            new_image.paste(image, (0, 0))
            image = new_image
            width = new_width
        
        # Convert image to byte array
        img_bytes = []
        for y in range(img_height):
            for x in range(0, width, 8):
                byte_val = 0
                for bit in range(8):
                    pixel = image.getpixel((x + bit, y))
                    if pixel == 0:  # Black pixel
                        byte_val |= (1 << (7 - bit))
                img_bytes.append(byte_val)
        
        # Print to thermal printer
        hPrinter = win32print.OpenPrinter(printer_name)
        doc_info = ("Bilingual Print", None, "RAW")
        win32print.StartDocPrinter(hPrinter, 1, doc_info)
        win32print.StartPagePrinter(hPrinter)
        
        # Initialize printer
        win32print.WritePrinter(hPrinter, ESC_INIT)
        
        # GS v 0 command: Print raster bitmap
        width_bytes = width // 8
        xL = width_bytes & 0xFF
        xH = (width_bytes >> 8) & 0xFF
        yL = img_height & 0xFF
        yH = (img_height >> 8) & 0xFF
        
        cmd = bytes([0x1D, 0x76, 0x30, 0x00, xL, xH, yL, yH])
        win32print.WritePrinter(hPrinter, cmd)
        win32print.WritePrinter(hPrinter, bytes(img_bytes))
        
        # Line feed
        win32print.WritePrinter(hPrinter, b"\n")
        
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
        win32print.ClosePrinter(hPrinter)
        
        return True, "Printed successfully"
    except Exception as e:
        return False, f"Error: {str(e)}"





@pos_printer_v6_api.route("/end-shift", methods=["POST"]) 
def end_shift_report_route():
    from flask import request, jsonify

    try:
        data = request.get_json()
        end_shift_report(data,flask_mode=True)

        return jsonify({
            "status": True,
            "message": "Print job executed"
        }), 200

    except ValueError as e:
        return jsonify({
            "status": False,
            "message": str(e)
        }), 400

    except Exception as e:
        logger.exception(e)
        return jsonify({
            "status": False,
            "message": "Internal server error"
        }), 500

def end_shift_report(data,flask_mode =False):
    """
    Print cashier end of shift report
    
    Request body:
    {
        "printer_name": "Your Printer Name",
        "branch_name": "Test branch",
        "cashier_name": "ANIKUTTAN",
        "report_date": "15-Dec-2025 10:55 AM",
        "transaction_date": "05-Dec-2025",
        "total_sales": 0.000,
        "refund_amount": 0.000,
        "net_sales": 0.000,
        "card_amount": 0.000,
        "cash_amount": 0.000,
        "cash_float": 12.000,
        "cash_in_drawer": 12.000,
        "over_short": 0.000,
        "include_arabic": false  // Optional: set to true to include Arabic labels
    }
    """

 
    if not data or not data.get("printer_name"):
        if flask_mode:
            from flask import jsonify
            return jsonify({
                "status": False,
                "statusCode": 400,
                "message": "Missing printer_name or receipt_data"
            }), 400
        else:
            logger.error("Missing printer_name or receipt_data")
            return   
 
        
    
    
    if not data or not data.get("printer_name"):
        return jsonify({
            "status": False,
            "statusCode": 400,
            "message": "Missing printer_name"
        }), 400
    
    printer_name = data.get("printer_name")
    include_arabic = data.get("include_arabic", False)
    
    # Default values
    branch_name = data.get("branch_name", "Test branch")
    title = data.get("title", "SHIFT REPORT")
    cashier_name = data.get("cashier_name", "CASHIER")
    report_date = data.get("report_date", "")
    transaction_date = data.get("transaction_date", "")
    
    # Financial data
    total_sales = data.get("total_sales", 0.0)
    refund_amount = data.get("refund_amount", 0.0)
    net_sales = data.get("net_sales", 0.0)
    card_amount = data.get("card_amount", 0.0)
    cash_amount = data.get("cash_amount", 0.0)
    cash_float = data.get("cash_float", 0.0)
    cash_in_drawer = data.get("cash_in_drawer", 0.0)
    over_short = data.get("over_short", 0.0)
    
    # Arabic labels (only used if include_arabic is True)
    arabic_labels = {
        "branch": "الفرع",
        "cashier": "الكاشير",
        "transaction_date": "تاريخ المعاملة",
        "total_sales": "إجمالي المبيعات",
        "refund": "المبلغ المسترد",
        "net_sales": "صافي المبيعات",
        "card": "مبلغ البطاقة",
        "cash": "المبلغ النقدي",
        "float": "العوامة النقدية",
        "drawer": "النقد في الدرج",
        "over_short": "زيادة/نقص"
    }
    
    try:
        hPrinter = win32print.OpenPrinter(printer_name)
        doc_info = ("End Shift Report", None, "RAW")
        win32print.StartDocPrinter(hPrinter, 1, doc_info)
        win32print.StartPagePrinter(hPrinter)
        
        win32print.WritePrinter(hPrinter, ESC_INIT)
        
        # Title 
        img_bytes, w, h = print_text_line(printer_name, title, font_size=28, align='center')
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        win32print.WritePrinter(hPrinter, b"\n")
        
        # Branch name
        img_bytes, w, h = print_text_line(printer_name, branch_name, font_size=24, align='center')
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        win32print.WritePrinter(hPrinter, b"\n")
        
        # Cashier Name
        cashier_label = "Cashier Name:"
        cashier_text = f"{cashier_label} {cashier_name}"
        img_bytes, w, h = print_text_line(printer_name, cashier_text, font_size=22, align='center')
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        win32print.WritePrinter(hPrinter, b"\n")
        
        # Report Date
        if report_date:
            img_bytes, w, h = print_text_line(printer_name, report_date, font_size=20, align='center')
            if img_bytes:
                send_bitmap(hPrinter, img_bytes, w, h)
        
        # Transaction Date
        if transaction_date:
            trans_text = f"Transation Date: {transaction_date}"
            img_bytes, w, h = print_text_line(printer_name, trans_text, font_size=20, align='center')
            if img_bytes:
                send_bitmap(hPrinter, img_bytes, w, h)
        
        # Separator line
        img_bytes, w, h = print_dashed_line()
        send_bitmap(hPrinter, img_bytes, w, h)
        
        win32print.WritePrinter(hPrinter, b"\n")
        
        # Financial details
        
        # Total Sales
        img_bytes, w, h = print_end_shift_line(
            "Total Sales :",
            f"{total_sales:.3f} KWD",
            font_size=22,
            arabic_label=arabic_labels["total_sales"] if include_arabic else ""
        )
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        # Refund Amount
        img_bytes, w, h = print_end_shift_line(
            "Refund Amount :",
            f"{refund_amount:.3f} KWD",
            font_size=22,
            arabic_label=arabic_labels["refund"] if include_arabic else ""
        )
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        # Net Sales (Bold/Larger font)
        img_bytes, w, h = print_end_shift_line(
            "Net Sales :",
            f"{net_sales:.3f} KWD",
            font_size=24,
            arabic_label=arabic_labels["net_sales"] if include_arabic else ""
        )
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        # Card Amount
        img_bytes, w, h = print_end_shift_line(
            "Card Amount :",
            f"{card_amount:.3f} KWD",
            font_size=22,
            arabic_label=arabic_labels["card"] if include_arabic else ""
        )
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        # Cash Amount
        img_bytes, w, h = print_end_shift_line(
            "Cash Amount :",
            f"{cash_amount:.3f} KWD",
            font_size=22,
            arabic_label=arabic_labels["cash"] if include_arabic else ""
        )
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        # Cash Float
        img_bytes, w, h = print_end_shift_line(
            "Cash Float :",
            f"{cash_float:.3f} KWD",
            font_size=22,
            arabic_label=arabic_labels["float"] if include_arabic else ""
        )
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        # Cash In Drawer
        img_bytes, w, h = print_end_shift_line(
            "Cash In Drawer :",
            f"{cash_in_drawer:.3f} KWD",
            font_size=22,
            arabic_label=arabic_labels["drawer"] if include_arabic else ""
        )
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        # Over/Short
        img_bytes, w, h = print_end_shift_line(
            "Over/Short :",
            f"{over_short:.3f} KWD",
            font_size=22,
            arabic_label=arabic_labels["over_short"] if include_arabic else ""
        )
        if img_bytes:
            send_bitmap(hPrinter, img_bytes, w, h)
        
        # Final paper feed
        win32print.WritePrinter(hPrinter, b"\n\n\n\n")
        
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
        win32print.ClosePrinter(hPrinter)
        
        return jsonify({
            "status": True,
            "statusCode": 200,
            "message": f"End shift report printed successfully on printer: {printer_name}"
        }), 200
        
    except Exception as e:
        logger.error(f"End shift print error: {e}")
        return jsonify({
            "status": False,
            "statusCode": 500,
            "message": f"Print error: {str(e)}"
        }), 500


@pos_printer_v6_api.route("/print-sample-list", methods=["POST"])
def print_sample_list():
    """
    Print multiple English/Arabic pairs in a list format.
    
    Request body:
    {
        "printer_name": "Your Printer Name",
        "items": [
            {"english": "Shirt", "arabic": "قميص"},
            {"english": "Pants", "arabic": "بنطلون"},
            {"english": "Dress", "arabic": "فستان"},
            {"english": "Jacket", "arabic": "سترة"},
            {"english": "Shoes", "arabic": "حذاء"}
        ],
        "font_size": 30,
        "align": "left"
    }
    
    font_size: 20-60 (default 30)
    align: "left", "center", "right" (default "left")
    
    Output:
    Shirt / قميص
    Pants / بنطلون
    Dress / فستان
    Jacket / سترة
    Shoes / حذاء
    """
    data = request.get_json()
    
    # Validate request
    if not data or not data.get("printer_name") or not data.get("items"):
        return jsonify({
            "status": False,
            "statusCode": 400,
            "message": "Missing printer_name or items"
        }), 400
    
    printer_name = data.get("printer_name")
    items = data.get("items")
    font_size = data.get("font_size", 30)
    align = data.get("align", "left")
    
    # Validate items array
    if not isinstance(items, list) or len(items) == 0:
        return jsonify({
            "status": False,
            "statusCode": 400,
            "message": "items must be a non-empty array"
        }), 400
    
    try:
        # Print each bilingual item
        for item in items:
            english = item.get("english", "")
            arabic = item.get("arabic", "")
            
            if not english or not arabic:
                continue  # Skip invalid items
            
            success, msg = print_bilingual_text(printer_name, english, arabic, font_size, align)
            
            if not success:
                return jsonify({
                    "status": False,
                    "statusCode": 500,
                    "message": f"Failed at '{english}': {msg}"
                }), 500
        
        # Final paper feed
        hPrinter = win32print.OpenPrinter(printer_name)
        doc_info = ("List End", None, "RAW")
        win32print.StartDocPrinter(hPrinter, 1, doc_info)
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, b"\n\n\n")  # Feed paper for cutting
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
        win32print.ClosePrinter(hPrinter)
        
        return jsonify({
            "status": True,
            "statusCode": 200,
            "message": f"Successfully printed {len(items)} bilingual items"
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": False,
            "statusCode": 500,
            "message": f"Print error: {str(e)}"
        }), 500