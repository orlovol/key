import os

from flask import jsonify

from key.core import engine


class SearchEngine:
    def __init__(self, app=None):
        self.app = app

        csv = os.getenv("GEODATA")
        self.engine = engine.Engine(file=csv)

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["search_engine"] = self

    def query(self, string):
        results = self.engine.search(string)
        return jsonify(results)


# init here, but could be in extensions.py
search_engine = SearchEngine()
