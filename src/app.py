import os
import sys
import threading
from dotenv import load_dotenv
from flask import Flask, json, jsonify
import urllib
from waitress import serve
from urllib.parse import urlparse, parse_qs 
 
from src.utils.logger import logger
from src.utils.tray import start_tray
from src.printer_routes import get_routes
from src.printer_routes.epos_printer_v6 import print_receipt
 


# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

app = Flask(__name__)

for route in get_routes():
    app.register_blueprint(route)
 
 
def handle_url_command(url_string):
    try:
        parsed_url = urlparse(url_string)
        command_from_path = parsed_url.path.strip('/')
        command_from_host = parsed_url.netloc.split(':')[0] 

        command = command_from_path if command_from_path else command_from_host
        if not command:
            command = "unknown"

        logger.info(f"Agent launched via Custom URL Scheme. Command detected: {command}")

        if command == 'ping':
            logger.info("Custom URL 'ping' received successfully. Server VERSION v7.6.0 Exiting.")

        elif command == 'print':
            logger.info("Custom URL 'print' received successfully. Server VERSION v7.6.0")
            query_params = parse_qs(parsed_url.query)

            # Extract printer name
            printer_name = query_params.get("printer_name", [""])[0]

            # Extract and decode nested receipt data
            data_json = query_params.get("data", ["{}"])[0]
            receipt_data = json.loads(urllib.parse.unquote(data_json))

            # Build the data dictionary expected by print_receipt
            data = {
                "printer_name": printer_name,
                "receipt_data": receipt_data
            }

            # Call your printing function
            print_receipt(data, flask_mode=False)

            logger.info(f"Executed print job for printer: {printer_name}")

        else:
            logger.info(f"Unknown custom URL command received: {command}")

    except Exception as e:
        logger.info(f"Error handling custom URL command: {e}")

    sys.exit(0)

if __name__ == "__main__":
 
    if len(sys.argv) > 1:
      
        handle_url_command(sys.argv[1])
        sys.exit(0)
        
        
    # --- START BACKGROUND SERVICES AND SERVER (Default Mode) ---
    
    port = int(os.getenv("PORT", 5009))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    use_waitress = os.getenv("USE_WAITRESS", "false").lower() == "true"
    
    # 1. Start Tray Icon
    threading.Thread(target=start_tray, daemon=True).start()
    
  
    # 3. Start Flask/Waitress Server (runs local API/status checks)
    logger.info("Agent starting in Full Background Mode (Server + WebSocket).")
    
    if use_waitress:
        logger.info(f"Application running on Prod server at 127.0.0.1:{port} VERSION v7.6.4")
        serve(app, host="127.0.0.1", port=port)
    else:
        logger.info(f"Application running on dev server at 127.0.0.1:{port}")
        app.run(host="127.0.0.1", port=port, debug=debug, use_reloader=debug)
 