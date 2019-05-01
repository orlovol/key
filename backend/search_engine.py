import os
import pathlib

from flask import jsonify

from key.core import engine


class SearchEngine:
    def __init__(self, app=None):
        self.app = app

        csv = os.getenv("GEODATA")
        csv_path = pathlib.Path(__file__).parents[1] / csv
        self.engine = engine.Engine(file=csv_path)

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
