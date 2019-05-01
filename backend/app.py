from dotenv import load_dotenv
load_dotenv()

from flask import Flask

from .api import api
from .search_engine import search_engine

app = Flask(__name__.split(".")[0], static_folder=None)
app.register_blueprint(api)
search_engine.init_app(app)
