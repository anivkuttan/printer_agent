import os
import sys
import threading
from dotenv import load_dotenv
from flask import Flask, json, jsonify 
from flask_cors import CORS
from waitress import serve
from urllib.parse import parse_qsl, urlparse, parse_qs 
 
from src.utils.logger import logger
from src.utils.tray import start_tray
from src.printer_routes import get_routes
from src.printer_routes.epos_printer_v6 import end_shift_report, print_receipt
from src.utils.version import __version__


# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": "*"}},  # dev-friendly
)
for route in get_routes():
    app.register_blueprint(route)
 

if __name__ == "__main__":
  
    port = int(os.getenv("PORT",5003))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    use_waitress = os.getenv("USE_WAITRESS", "false").lower() == "true"
    
    # 1. Start Tray Icon
    threading.Thread(target=start_tray, daemon=True).start()
    
    if use_waitress:
        log_message = f"Application running on PROD server at 127.0.0.1:{port} VERSION v{__version__}"
        logger.info(log_message)
        print(log_message)
        serve(app, host="127.0.0.1", port=port)
    else:
      
        log_message = f"Application running on DEV server at 127.0.0.1:{port} VERSION v{__version__}"
        logger.info(log_message)
        print(log_message)
        app.run(host="127.0.0.1", port=port, debug=debug, use_reloader=debug)
 