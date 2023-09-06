KEYBINDS = {
    "open-freeform": "q",
    "closed-freeform": "w",
    "line": "e",
    "circle": "r",
    "rectangle": "t",
    "pan-and-zoom": "a",
    "erase": "s",
    "slice-right": "ArrowRight",
    "slice-left": "ArrowLeft",
}

ANNOT_ICONS = {
    "open-freeform": "mdi:draw",
    "closed-freeform": "fluent:draw-shape-20-filled",
    "line": "pepicons-pop:line-y",
    "circle": "gg:shape-circle",
    "rectangle": "gg:shape-square",
    "eraser": "ph:eraser",
    "pan-and-zoom": "material-symbols:drag-pan-rounded",
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
    "pan-and-zoom": "Pan and zoom mode",
    "slice-right": "Next slice",
    "slice-left": "Previous slice",
}

KEY_MODES = {
    KEYBINDS["open-freeform"]: ("drawopenpath", "open-freeform"),
    KEYBINDS["closed-freeform"]: ("drawclosedpath", "closed-freeform"),
    KEYBINDS["circle"]: ("drawcircle", "circle"),
    KEYBINDS["rectangle"]: ("drawrect", "rectangle"),
    KEYBINDS["line"]: ("drawline", "line"),
    KEYBINDS["pan-and-zoom"]: ("pan", "pan-and-zoom"),
    KEYBINDS["erase"]: ("eraseshape", "eraser"),
}
