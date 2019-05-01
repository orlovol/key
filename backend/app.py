from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_cors import CORS

from .api import api
from .search_engine import search_engine

app = Flask(__name__.split(".")[0], static_folder=None)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

app.register_blueprint(api)
search_engine.init_app(app)
