 
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
 
from src.printer_routes import printer_api
from src.tray import start_tray
load_dotenv() 

app = Flask(__name__)
CORS(app)
app.register_blueprint(printer_api)



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