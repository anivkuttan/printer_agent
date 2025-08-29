import os
import sys
from dotenv import load_dotenv
from flask_cors import CORS
from flask import Flask, jsonify

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.tray import start_tray
from src.printer_routes import get_routes

load_dotenv()

app = Flask(__name__)
CORS(app)
for route in get_routes():
    app.register_blueprint(route)


if __name__ == "__main__":
    import os
    import threading
    from waitress import serve

    port = int(os.getenv("PORT", 5008))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    use_waitress = os.getenv("USE_WAITRESS", "false").lower() == "true"

    # Start tray icon in a background thread
    threading.Thread(target=start_tray, daemon=True).start()

    if use_waitress:
        # Production: use Waitress
        serve(app, host="127.0.0.1", port=port)
    else:
        # Development: use Flask dev server
        app.run(host="127.0.0.1", port=port, debug=debug, use_reloader=debug)
