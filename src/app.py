import os
from flask import Flask
from flask_cors import CORS
import threading
from src.printer_routes import printer_api
from src.tray import start_tray

app = Flask(__name__)
CORS(app)
app.register_blueprint(printer_api)

 
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    threading.Thread(target=start_tray, daemon=True).start()
    app.run(host="127.0.0.1", port=port, debug=debug, use_reloader=False)