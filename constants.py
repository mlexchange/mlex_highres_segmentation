import os
from tiled.client import from_uri
from dotenv import load_dotenv

load_dotenv()

TILED_URI = os.getenv("TILED_URI")
API_KEY = os.getenv("API_KEY")

if os.getenv("SERVE_LOCALLY", False):
    DATA = from_uri("http://localhost:8000")
else:
    CLIENT = from_uri(TILED_URI, api_key=API_KEY)
    DATA = CLIENT["data"]
