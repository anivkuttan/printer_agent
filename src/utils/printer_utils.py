import base64
import os
import time
import win32print
import pdfkit
import win32api
count = 0


def list_printers():
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    printers = win32print.EnumPrinters(flags)
    return [printer[2] for printer in printers]


# def get_default_printer():
#     return win32print.GetDefaultPrinter()


# def set_default_printer(printer_name):
#     win32print.SetDefaultPrinter(printer_name)
def get_default_printer():
    try:
        return win32print.GetDefaultPrinter()
    except Exception as e:
        return None  # or handle the error appropriately


def set_default_printer(printer_name):
    try:
        win32print.SetDefaultPrinter(printer_name)
        return True
    except Exception as e:
        return False  # or raise with more context


def safe_base64_decode(data):
    data = data.strip()
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    return base64.b64decode(data)


# def printer_exists(printer_name):
#     """Check if a printer exists"""
#     available_printers = list_printers()
#     return printer_name in available_printers


# def get_printer_status(printer_name):
#     """Get printer status information"""
#     try:
#         printer_info = win32print.GetPrinter(
#             win32print.OpenPrinter(printer_name), 2)
#         return {
#             'status': printer_info['Status'],
#             'jobs': printer_info['cJobs'],
#             'printer_name': printer_info['pPrinterName']
#         }
#     except Exception as e:
#         return None
