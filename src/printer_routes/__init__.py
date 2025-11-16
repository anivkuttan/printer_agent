from flask import Blueprint
from flask import Blueprint
from .health import health_api
from .printers import printer_api
from .epos_printer import pos_printer_api
from .epos_printer_v2 import pos_printer_v2_api
from .epos_printer_v3 import pos_printer_v3_api
from .epos_printer_v6 import pos_printer_v6_api

# Master blueprint to register all printer routes
all_printers_api = Blueprint("all_printers_api", __name__)
all_printers_api.register_blueprint(health_api)
all_printers_api.register_blueprint(printer_api)
all_printers_api.register_blueprint(pos_printer_api)
all_printers_api.register_blueprint(pos_printer_v2_api)
all_printers_api.register_blueprint(pos_printer_v3_api)
all_printers_api.register_blueprint(pos_printer_v6_api)


def get_routes():
    return [health_api, printer_api, pos_printer_api, pos_printer_v2_api, pos_printer_v3_api,pos_printer_v6_api]
