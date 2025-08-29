
# from flask import Blueprint
# from .tray import create_tray_image, start_tray
# from .version import __version__

# # Master blueprint to register all printer routes
# all_printers_api = Blueprint("all_printers_api", __name__)
# all_printers_api.register_blueprint(create_tray_image)
# all_printers_api.register_blueprint(start_tray)
# all_printers_api.register_blueprint(__version__)


# def get_routes():
#     return [create_tray_image, start_tray, __version__]

# __all__ = ["list_printers", "get_default_printer",
#            "set_default_printer", "safe_base64_decode", "__version__"]
