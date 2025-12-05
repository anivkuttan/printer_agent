from flask_sock import Sock
import json

from src.utils.version import __version__

def register_websocket_routes(app):
    sock = Sock(app)

    @sock.route('/ws')
    def websocket_connection(ws):
        print("Client connected to WebSocket")

        # Example: send version every 1 sec
        while True:
            ws.send(json.dumps({
                "type": "status",
                "version": __version__,
                "connected": True
            }))
