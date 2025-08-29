from src.printer_routes import get_routes
from src.utils.tray import start_tray
import os
import sys
from dotenv import load_dotenv
from flask_cors import CORS
from flask import Flask
from logging.handlers import RotatingFileHandler

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


load_dotenv()

app = Flask(__name__)
CORS(app)
for route in get_routes():
    app.register_blueprint(route)


if __name__ == "__main__":
    import os
    import threading
    from waitress import serve

    port = int(os.getenv("PORT", 5009))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    use_waitress = os.getenv("USE_WAITRESS", "False").lower() == "true"

    # Start tray icon in a background thread
    threading.Thread(target=start_tray, daemon=True).start()

    if use_waitress:
        # Production: use Waitress
        print(f"Starting with Waitress (production mode)...{port}")
        serve(app, host="127.0.0.1", port=port)
    else:
        print(f"Starting with Flask dev server (debug mode)...{port}")
        # Development: use Flask dev server
        app.run(host="127.0.0.1", port=port, debug=debug, use_reloader=debug)
