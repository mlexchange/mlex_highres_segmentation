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


KEYBINDS = {
    "open-freeform": "q",
    "closed-freeform": "w",
    "line": "e",
    "circle": "r",
    "rectangle": "t",
    "pan-and-zoom": "a",
    "erase": "s",
    "delete-all": "d",
    "slice-right": "ArrowRight",
    "slice-left": "ArrowLeft",
    "classes": [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
    ],
}

ANNOT_ICONS = {
    "open-freeform": "mdi:draw",
    "closed-freeform": "fluent:draw-shape-20-regular",
    "line": "pepicons-pop:line-y",
    "circle": "gg:shape-circle",
    "rectangle": "gg:shape-square",
    "eraser": "ph:eraser",
    "delete-all": "octicon:trash-24",
    "pan-and-zoom": "el:off",
    "slice-right": "line-md:arrow-right",
    "slice-left": "line-md:arrow-left",
}

ANNOT_NOTIFICATION_MSGS = {
    "open-freeform": "Open freeform annotation mode",
    "closed-freeform": "Closed freeform annotation mode",
    "line": "Line annotation mode",
    "circle": "Circle annotation mode",
    "rectangle": "Rectangle annotation mode",
    "eraser": "Eraser annotation mode",
    "delete-all": "Delete all annotations",
    "pan-and-zoom": "Pan and zoom mode",
    "slice-right": "Next slice",
    "slice-left": "Previous slice",
}
