from src.printer_routes import get_routes
from src.utils.tray import start_tray
import os
import sys
import time
from dotenv import load_dotenv
from flask_cors import CORS, cross_origin
from flask import Flask, jsonify, request, make_response

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

app = Flask(__name__)

CORS(app, 
     resources={r"/*": {
         "origins": "*",
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": "*",
         "supports_credentials": False
     }})

@app.after_request
def add_cors_headers(response):
    
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600" 
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    
    return response

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*" 
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        
        return response
 
for route in get_routes():
    app.register_blueprint(route)

if __name__ == "__main__":
    import threading
    from waitress import serve

    port = int(os.getenv("PORT", 5009))
    use_waitress = os.getenv("USE_WAITRESS", "True").lower() == "true"

    threading.Thread(target=start_tray, daemon=True).start()

 
    print(f"Starting on http://0.0.0.0:{port}")
    print(f"CORS: Enabled for ALL origins (*)")
    print(f"Private Network Access: Enabled")
    
    if use_waitress:
        print(f"Mode: Production (Waitress)")
        serve(app, host="0.0.0.0", port=port, threads=4)
    else:
        print(f"Mode: Development (Flask)")
        app.run(host="0.0.0.0", port=port, debug=False)