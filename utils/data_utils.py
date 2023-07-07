import os
import requests
from urllib.parse import urlparse

from tiled.client import from_uri
from tiled.client.cache import Cache
import config

client = from_uri(config.tiled_uri, api_key=config.api_key)
data = client["data"]


def get_data_project_names():
    return list(data)


def convert_hex_to_rgba(hex, alpha=0.3):
    return f"rgba{tuple(int(hex[i:i+2], 16) for i in (1, 3, 5)) + (alpha,)}"
