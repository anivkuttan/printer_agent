
from flask import Blueprint
from .health import health_api
from .printers import printer_api
from .epos_printer import pos_printer_api

# Master blueprint to register all printer routes
all_printers_api = Blueprint("all_printers_api", __name__)
all_printers_api.register_blueprint(health_api)
all_printers_api.register_blueprint(printer_api)
all_printers_api.register_blueprint(pos_printer_api)


def get_routes():
    return [health_api, printer_api, pos_printer_api]
