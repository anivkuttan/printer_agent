import os
import sys
import threading
import time
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from waitress import serve
  
from src.utils.tray import start_tray 
from src.utils.version import __version__
from src.ws_client import start_ws_client, ws_health_logger 

 
# project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

load_dotenv()

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "*"}}
)
 
 

if __name__ == "__main__": 
    threading.Thread(target=start_tray, daemon=True).start()

   
    threading.Thread(target=start_ws_client, daemon=True).start()
    threading.Thread(target=ws_health_logger, daemon=True).start() 
    while True:
        time.sleep(1)