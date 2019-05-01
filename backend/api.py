from flask import Blueprint, request

from .search_engine import search_engine

api = Blueprint("api", __name__, url_prefix="/api/v1")


@api.route("/search")
def search():
    query = request.args.get("q", "")
    return search_engine.query(query) if query else ""
