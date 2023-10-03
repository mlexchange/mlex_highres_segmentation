KEYBINDS = {
    "closed-freeform": "q",
    "circle": "w",
    "rectangle": "e",
    "pan-and-zoom": "a",
    "erase": "s",
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
    "closed-freeform": "fluent:draw-shape-20-filled",
    "circle": "gg:shape-circle",
    "rectangle": "gg:shape-square",
    "eraser": "ph:eraser",
    "pan-and-zoom": "material-symbols:drag-pan-rounded",
    "slice-right": "line-md:arrow-right",
    "slice-left": "line-md:arrow-left",
    "jump-to-slice": "mdi:arrow",
    "export-annotation": "entypo:export",
    "no-more-slices": "pajamas:warning-solid",
    "export": "entypo:export",
}

ANNOT_NOTIFICATION_MSGS = {
    "closed-freeform": "Closed freeform annotation mode",
    "circle": "Circle annotation mode",
    "rectangle": "Rectangle annotation mode",
    "eraser": "Eraser annotation mode",
    "pan-and-zoom": "Pan and zoom mode",
    "slice-right": "Next slice",
    "slice-left": "Previous slice",
    "slice-jump": "Jumped to slice",
    "export": "Annotation Exported!",
    "export-msg": "Succesfully exported in .json format.",
    "export-fail": "No Annotations to Export!",
    "export-fail-msg": "Please annotate an image before exporting.",
}

KEY_MODES = {
    KEYBINDS["closed-freeform"]: ("drawclosedpath", "closed-freeform"),
    KEYBINDS["circle"]: ("drawcircle", "circle"),
    KEYBINDS["rectangle"]: ("drawrect", "rectangle"),
    KEYBINDS["pan-and-zoom"]: ("pan", "pan-and-zoom"),
    KEYBINDS["erase"]: ("eraseshape", "eraser"),
}
