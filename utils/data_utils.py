import os
import json
import requests
from urllib.parse import urlparse

from tiled.client import from_uri
from tiled.client.cache import Cache
from dotenv import load_dotenv

load_dotenv()

TILED_URI = os.getenv("TILED_URI")
API_KEY = os.getenv("API_KEY")

client = from_uri(TILED_URI, api_key=API_KEY)
data = client["data"]


def get_data_project_names():
    return list(data)


def convert_hex_to_rgba(hex, alpha=0.3):
    return f"rgba{tuple(int(hex[i:i+2], 16) for i in (1, 3, 5)) + (alpha,)}"


def DEV_load_exported_json_data(file_path, USER_NAME, IMAGE_SRC):
    DATA_JSON = []

    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                json_data = json.loads(line)
                json_data["data"] = json.loads(json_data["data"])
                DATA_JSON.append(json_data)

    data = [
        data
        for data in DATA_JSON
        if data["user"] == USER_NAME and data["source"] == IMAGE_SRC
    ]
    if data:
        data = sorted(data, key=lambda x: x["time"], reverse=True)

    return data


def DEV_filter_json_data_by_timestamp(data, timestamp):
    return [data for data in data if data["time"] == timestamp]
