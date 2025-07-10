import win32print

def list_printers():
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    printers = win32print.EnumPrinters(flags)
    return [printer[2] for printer in printers]

def get_default_printer():
    return win32print.GetDefaultPrinter()

def set_default_printer(printer_name):
    win32print.SetDefaultPrinter(printer_name)
