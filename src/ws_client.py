import json
import time
import websocket
 
from src.printer_routes.health import get_version,ping
from src.printer_routes.printers import  get_printers,get_default_printer
from src.printer_routes.epos_printer_v6 import end_shift_report, print_receipt
from src.utils.logger import logger 
from src.utils.version import __version__
WS_CONNECTED = False
# Node.js WS server URL
WS_URL = "ws://13.126.157.19/api/ws/"  
PRINTER_ID = "BRANCH_02"        

def on_message(ws, message):
    """Handle incoming print jobs from Node.js backend"""
    try:
        data = json.loads(message)
        logger.info(f"Received WS message: {data}")

        if data["type"] == "RECEIPT":
            logger.debug("[WS_HEARTBEAT] RECEIPT received")
            print("[WS_HEARTBEAT] RECEIPT received")
            print_receipt(data["payload"])

        elif data["type"] == "SHIFT_REPORT":
            logger.debug("[WS_HEARTBEAT] SHIFT_REPORT received")
            print("[WS_HEARTBEAT] SHIFT_REPORT received")
            end_shift_report(data["payload"])

        elif data["type"] == "GET_AVALABLE_PRINTERS":
            logger.debug("[WS_HEARTBEAT] GET_AVALABLE_PRINTERS received")
            print("[WS_HEARTBEAT] GET_AVALABLE_PRINTERS received")
            return_data = get_printers()
            ws.send(json.dumps({
                "event": "INFO",
                "jobId": data["jobId"],
                "printerId": PRINTER_ID,
                "return_data":return_data
                }))
            return;
    
        elif data["type"] == "GET_DEFAULT_PRINTERS":
            logger.debug("[WS_HEARTBEAT] GET_DEFAULT_PRINTERS received")
            print("[WS_HEARTBEAT] GET_DEFAULT_PRINTERS received")
            return_data = get_default_printer()
            ws.send(json.dumps({
                "event": "INFO",
                "jobId": data["jobId"],
                "printerId": PRINTER_ID,
                "return_data":return_data
                }))
            return;
    
        elif data["type"] == "PING":
            logger.debug("[WS_HEARTBEAT] Ping received")
            print("[WS_HEARTBEAT] Ping received")
            return_data = ping()
            ws.send(json.dumps({
                "event": "INFO",
                "jobId": data["jobId"],
                "printerId": PRINTER_ID,
                "return_data":return_data
                }))
            return;
           
        elif data["type"] == "VERSION":
          
            logger.debug("[WS_HEARTBEAT] VERSION received")
            print("[WS_HEARTBEAT] VERSION received")
            return_data = get_version()
            ws.send(json.dumps({
                "event": "INFO",
                "jobId": data["jobId"],
                "printerId": PRINTER_ID,
                "return_data":return_data
                }))
            return;

        # Notify backend that printing is done
        ws.send(json.dumps({
            "event": "PRINT_DONE",
            "jobId": data["jobId"],
            "printerId": PRINTER_ID
        }))

    except Exception as e:
        logger.error(f"Error processing print job: {e}")
        ws.send(json.dumps({
            "event": "PRINT_FAILED",
            "jobId": data.get("jobId", None),
            "error": str(e),
            "printerId": PRINTER_ID
        }))

def on_open(ws):
    global WS_CONNECTED
    WS_CONNECTED = True

    logger.info(
        f"[WS_CONNECTED] Connected to backend: {WS_URL} Version: {__version__}"
    )
    print(
        f"[WS_CONNECTED] Connected to backend: {WS_URL} Version: {__version__}"
    )

    ws.send(json.dumps({
        "event": "REGISTER_PRINTER",
        "printerId": PRINTER_ID
    }))

    logger.info(
        f"[WS_REGISTER_SENT] PrinterId={PRINTER_ID}"
    )

    print(
        f"[WS_REGISTER_SENT] PrinterId={PRINTER_ID}"
    )

def on_close(ws, close_status_code, close_msg):
    global WS_CONNECTED
    WS_CONNECTED = False

    logger.warning(
        f"[WS_CLOSED] code={close_status_code} reason={close_msg}"
    )
    print(
        f"[WS_CLOSED] code={close_status_code} reason={close_msg}"
    )

def on_error(ws, error):
    logger.error(
        f"[WS_ERROR] {error}"
    )
    print(
        f"[WS_ERROR] {error}"
    )

def start_ws_client():
    logger.info("[WS_CLIENT] Starting WebSocket client...")
    print("[WS_CLIENT] Starting WebSocket client...")

    while True:
        try:
            logger.info(f"[WS_CONNECTING] {WS_URL}")
            print(f"[WS_CONNECTING] {WS_URL}")

            ws = websocket.WebSocketApp(
                WS_URL,
            
                on_open=on_open,
                on_message=on_message,
                on_close=on_close,
                on_error=on_error
            )
         

            ws.run_forever(
                ping_interval=20,
                ping_timeout=10 
            )

        except Exception as e:
            logger.exception(f"[WS_FATAL_ERROR] {e}")
            print(f"[WS_FATAL_ERROR] {e}")


        logger.info("[WS_RECONNECT] Retrying in 5 seconds...")
        print("[WS_RECONNECT] Retrying in 5 seconds...")
        time.sleep(5)

def ws_health_logger():
    while True:
        if WS_CONNECTED:
            print("[WS_STATUS] CONNECTED")
        else:
            print("[WS_STATUS] DISCONNECTED")
        time.sleep(30)