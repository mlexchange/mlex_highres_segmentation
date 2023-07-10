import os
import requests
from urllib.parse import urlparse

from tiled.client import from_uri
from tiled.client.cache import Cache
from tiled.client import show_logs
from dotenv import load_dotenv

load_dotenv()
show_logs()

TILED_URI = os.getenv("TILED_URI")
API_KEY = os.getenv("API_KEY")

client = from_uri(TILED_URI, api_key=API_KEY)
data = client["data"]


def get_data_project_names():
    return list(data)


def convert_hex_to_rgba(hex, alpha=0.3):
    return f"rgba{tuple(int(hex[i:i+2], 16) for i in (1, 3, 5)) + (alpha,)}"
