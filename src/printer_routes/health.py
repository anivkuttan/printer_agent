from flask import Blueprint, jsonify
from src.utils.version import __version__

health_api = Blueprint("health_api", __name__)


@health_api.route("/ping", methods=["GET"])
def ping():
    data = {
        "statusCode": 200,
        "status": True,
        "message": "Agent is running",
        "data": {"status": "ok", "version": __version__}
    }
    return jsonify(data), 200


@health_api.route("/version", methods=["GET"])
def get_version():
    data = {
        "statusCode": 200,
        "status": True,
        "message": "Agent is running",
        "data": {"version": __version__}
    }
    return jsonify(data)
