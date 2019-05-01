from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).parents[1]
for env in (".flaskenv", ".env"):
    load_dotenv(basedir / env)

from .app import app as application

__all__ = ["application"]
