from flask import Blueprint, jsonify
from ..utils.version import __version__

health_api = Blueprint("health_api", __name__)


@health_api.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "version": __version__}), 200


@health_api.route("/version", methods=["GET"])
def get_version():
    return jsonify({"version": __version__})



