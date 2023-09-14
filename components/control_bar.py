import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html
from dash_extensions import EventListener
from dash_iconify import DashIconify

from components.annotation_class import annotation_class_item
from constants import ANNOT_ICONS, KEYBINDS
from utils import data_utils


def _tooltip(text, children):
    """
    Returns a customized layout for a tooltip
    """
    return dmc.Tooltip(
        label=text, withArrow=True, position="top", color="#464646", children=children
    )


def _control_item(title, title_id, item):
    """
    Returns a customized layout for a control item
    """
    return dmc.Grid(
        [
            dmc.Text(
                title,
                id=title_id,
                size="sm",
                style={"width": "100px", "margin": "auto", "paddingRight": "5px"},
                align="right",
            ),
            html.Div(item, style={"width": "265px", "margin": "auto"}),
        ]
    )


def _accordion_item(title, icon, value, children, id, loading=True):
    """
    Returns a customized layout for an accordion item
    """
    if loading:
        panel = dmc.LoadingOverlay(
            dmc.AccordionPanel(children=children, id=id),
            loaderProps={"size": 0},
            overlayOpacity=0.4,
        )
    else:
        panel = dmc.AccordionPanel(children=children, id=id)
    return dmc.AccordionItem(
        [
            dmc.AccordionControl(
                title,
                icon=DashIconify(
                    icon=icon,
                    color="#00313C",
                    width=20,
                ),
            ),
            panel,
        ],
        value=value,
    )


def layout():
    """
    Returns the layout for the control panel in the app UI
    """
    DATA_OPTIONS = [
        item for item in data_utils.get_data_project_names() if "seg" not in item
    ]
    return drawer_section(
        dmc.Stack(
            style={"width": "400px"},
            children=[
                dmc.AccordionMultiple(
                    value=["data-select", "image-transformations", "annotations"],
                    children=[
                        _accordion_item(
                            "Data selection",
                            "majesticons:data-line",
                            "data-select",
                            id="data-selection-controls",
                            children=[
                                dmc.Space(h=5),
                                _control_item(
                                    "Dataset",
                                    "image-selector",
                                    dmc.Select(
                                        id="project-name-src",
                                        data=DATA_OPTIONS,
                                        value=DATA_OPTIONS[0] if DATA_OPTIONS else None,
                                        placeholder="Select an image to view...",
                                    ),
                                ),
                                dmc.Space(h=25),
                                _control_item(
                                    "Slice 1",
                                    "image-selection-text",
                                    [
                                        dmc.Grid(
                                            [
                                                dmc.Col(
                                                    _tooltip(
                                                        "Previous image",
                                                        children=dmc.ActionIcon(
                                                            DashIconify(
                                                                icon="ooui:previous-ltr",
                                                                width=10,
                                                            ),
                                                            variant="subtle",
                                                            size="sm",
                                                            id="image-selection-previous",
                                                        ),
                                                    ),
                                                    span=1,
                                                    style={
                                                        "margin": "auto",
                                                        "paddingRight": "0px",
                                                    },
                                                ),
                                                dmc.Col(
                                                    [
                                                        dmc.Slider(
                                                            min=1,
                                                            max=1000,
                                                            step=1,
                                                            value=25,
                                                            id="image-selection-slider",
                                                            size="sm",
                                                            color="gray",
                                                        ),
                                                    ],
                                                    span="auto",
                                                    style={"margin": "auto"},
                                                ),
                                                dmc.Col(
                                                    _tooltip(
                                                        "Next image",
                                                        children=dmc.ActionIcon(
                                                            DashIconify(
                                                                icon="ooui:previous-rtl",
                                                                width=10,
                                                            ),
                                                            variant="subtle",
                                                            id="image-selection-next",
                                                        ),
                                                    ),
                                                    span=1,
                                                    style={
                                                        "margin": "auto",
                                                        "paddingLeft": "0px",
                                                    },
                                                ),
                                            ]
                                        )
                                    ],
                                ),
                                dmc.Space(h=10),
                            ],
                        ),
                        _accordion_item(
                            "Image transformations",
                            "fluent-mdl2:image-pixel",
                            "image-transformations",
                            id="image-transformation-controls",
                            children=html.Div(
                                [
                                    dmc.Space(h=5),
                                    _control_item(
                                        "Brightness",
                                        "bightness-text",
                                        [
                                            dmc.Grid(
                                                [
                                                    dmc.Slider(
                                                        id={
                                                            "type": "slider",
                                                            "index": "brightness",
                                                        },
                                                        value=100,
                                                        min=0,
                                                        max=255,
                                                        step=1,
                                                        color="gray",
                                                        size="sm",
                                                        style={"width": "225px"},
                                                    ),
                                                    dmc.ActionIcon(
                                                        _tooltip(
                                                            "Reset brightness",
                                                            children=[
                                                                DashIconify(
                                                                    icon="fluent:arrow-reset-32-regular",
                                                                    width=15,
                                                                ),
                                                            ],
                                                        ),
                                                        size="xs",
                                                        variant="subtle",
                                                        id={
                                                            "type": "reset",
                                                            "index": "brightness",
                                                        },
                                                        n_clicks=0,
                                                        style={"margin": "auto"},
                                                    ),
                                                ],
                                                style={"margin": "0px"},
                                            )
                                        ],
                                    ),
                                    dmc.Space(h=20),
                                    _control_item(
                                        "Contrast",
                                        "contrast-text",
                                        dmc.Grid(
                                            [
                                                dmc.Slider(
                                                    id={
                                                        "type": "slider",
                                                        "index": "contrast",
                                                    },
                                                    value=100,
                                                    min=0,
                                                    max=255,
                                                    step=1,
                                                    color="gray",
                                                    size="sm",
                                                    style={"width": "225px"},
                                                ),
                                                dmc.ActionIcon(
                                                    _tooltip(
                                                        "Reset contrast",
                                                        children=[
                                                            DashIconify(
                                                                icon="fluent:arrow-reset-32-regular",
                                                                width=15,
                                                            ),
                                                        ],
                                                    ),
                                                    size="xs",
                                                    variant="subtle",
                                                    id={
                                                        "type": "reset",
                                                        "index": "contrast",
                                                    },
                                                    n_clicks=0,
                                                    style={"margin": "auto"},
                                                ),
                                            ],
                                            style={"margin": "0px"},
                                        ),
                                    ),
                                    dmc.Space(h=10),
                                ]
                            ),
                        ),
                        _accordion_item(
                            "Annotation tools",
                            "mdi:paintbrush-outline",
                            "annotations",
                            id="annotations-controls",
                            children=[
                                dmc.Text(
                                    "Drawing Toolbar",
                                    size="sm",
                                    align="right",
                                    color="#9EA4AB",
                                ),
                                dmc.Space(h=15),
                                dmc.Grid(
                                    [
                                        dmc.Space(w=8),
                                        html.Div(
                                            children=[
                                                _tooltip(
                                                    "Pan and zoom (A)",
                                                    dmc.ActionIcon(
                                                        id="pan-and-zoom",
                                                        variant="subtle",
                                                        color="gray",
                                                        children=DashIconify(
                                                            icon=ANNOT_ICONS[
                                                                "pan-and-zoom"
                                                            ],
                                                            width=20,
                                                        ),
                                                        size="lg",
                                                    ),
                                                ),
                                            ],
                                            className="flex-row",
                                            style={
                                                "justify-content": "space-evenly",
                                                "padding": "2.5px",
                                                "border": "1px solid #EAECEF",
                                                "border-radius": "5px",
                                            },
                                        ),
                                        dmc.Space(w=10),
                                        html.Div(
                                            children=[
                                                _tooltip(
                                                    "Open freeform (Q)",
                                                    dmc.ActionIcon(
                                                        id="open-freeform",
                                                        variant="subtle",
                                                        color="gray",
                                                        children=DashIconify(
                                                            icon=ANNOT_ICONS[
                                                                "open-freeform"
                                                            ],
                                                            width=20,
                                                        ),
                                                        style={
                                                            "backgroundColor": "#EAECEF"
                                                        },
                                                        size="lg",
                                                    ),
                                                ),
                                                _tooltip(
                                                    "Closed freeform (W)",
                                                    dmc.ActionIcon(
                                                        id="closed-freeform",
                                                        variant="subtle",
                                                        color="gray",
                                                        children=DashIconify(
                                                            icon=ANNOT_ICONS[
                                                                "closed-freeform"
                                                            ],
                                                            width=20,
                                                        ),
                                                        size="lg",
                                                    ),
                                                ),
                                                _tooltip(
                                                    "Line (E)",
                                                    dmc.ActionIcon(
                                                        id="line",
                                                        variant="subtle",
                                                        color="gray",
                                                        children=DashIconify(
                                                            icon="ci:line-l", width=20
                                                        ),
                                                        size="lg",
                                                    ),
                                                ),
                                                _tooltip(
                                                    "Circle (R)",
                                                    dmc.ActionIcon(
                                                        id="circle",
                                                        variant="subtle",
                                                        color="gray",
                                                        children=DashIconify(
                                                            icon=ANNOT_ICONS["circle"],
                                                            width=20,
                                                        ),
                                                        size="lg",
                                                    ),
                                                ),
                                                _tooltip(
                                                    "Rectangle (T)",
                                                    dmc.ActionIcon(
                                                        id="rectangle",
                                                        variant="subtle",
                                                        color="gray",
                                                        children=DashIconify(
                                                            icon=ANNOT_ICONS[
                                                                "rectangle"
                                                            ],
                                                            width=20,
                                                        ),
                                                        size="lg",
                                                    ),
                                                ),
                                                _tooltip(
                                                    "Eraser (S)",
                                                    dmc.ActionIcon(
                                                        id="eraser",
                                                        variant="subtle",
                                                        color="gray",
                                                        children=DashIconify(
                                                            icon=ANNOT_ICONS["eraser"],
                                                            width=20,
                                                        ),
                                                        size="lg",
                                                    ),
                                                ),
                                            ],
                                            className="flex-row",
                                            style={
                                                "width": "301px",
                                                "justify-content": "space-evenly",
                                                "padding": "2.5px",
                                                "border": "1px solid #EAECEF",
                                                "border-radius": "5px",
                                            },
                                        ),
                                    ]
                                ),
                                dmc.Space(h=30),
                                _control_item(
                                    "Drawing width",
                                    "paintbrush-text",
                                    dmc.Slider(
                                        id="paintbrush-width",
                                        value=5,
                                        min=1,
                                        max=20,
                                        step=1,
                                        color="gray",
                                        size="sm",
                                        style={"width": "257px"},
                                    ),
                                ),
                                dmc.Space(h=10),
                                dmc.Modal(
                                    title="Warning",
                                    id="delete-all-warning",
                                    children=[
                                        dmc.Text(
                                            "This action will permanently clear all annotations on this image frame. Are you sure you want to proceed?"
                                        ),
                                        dmc.Space(h=20),
                                        dmc.Group(
                                            [
                                                dmc.Button(
                                                    "Cancel",
                                                    id="modal-cancel-delete-button",
                                                ),
                                                dmc.Button(
                                                    "Continue",
                                                    color="red",
                                                    variant="outline",
                                                    id="modal-continue-delete-button",
                                                ),
                                            ],
                                            position="right",
                                        ),
                                    ],
                                ),
                                html.Div(
                                    [
                                        dmc.Text(
                                            "Manage Classes",
                                            size="sm",
                                            align="right",
                                            color="#9EA4AB",
                                        ),
                                        dmc.Space(h=10),
                                        html.Div(
                                            children=[
                                                annotation_class_item(
                                                    "#FFA200", "Class 1", []
                                                )
                                            ],
                                            id="annotation-class-container",
                                        ),
                                        dmc.Button(
                                            "+ Add new class... ",
                                            id="generate-annotation-class",
                                            variant="outline",
                                            style={
                                                "width": "100%",
                                            },
                                            className="add-class-btn",
                                        ),
                                        dmc.Space(h=20),
                                    ],
                                ),
                                dmc.Modal(
                                    id="generate-annotation-class-modal",
                                    title="Create a new annotation class",
                                    children=[
                                        html.Div(
                                            [
                                                dbc.Input(
                                                    type="color",
                                                    id="annotation-class-colorpicker",
                                                    style={"width": 75, "height": 50},
                                                    value="#DB0606",
                                                ),
                                                dmc.Space(w=25),
                                                html.Div(
                                                    [
                                                        dmc.TextInput(
                                                            id="annotation-class-label",
                                                            placeholder="Class label...",
                                                        ),
                                                        html.Div(
                                                            id="bad-label-color",
                                                            style={
                                                                "color": "red",
                                                                "fontSize": "12px",
                                                                "padding": "3px",
                                                            },
                                                        ),
                                                    ]
                                                ),
                                            ],
                                            style={
                                                "display": "flex",
                                                "justify-content": "flex-row",
                                                "align-items": "center",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                dmc.Button(
                                                    id="create-annotation-class",
                                                    children="Save",
                                                ),
                                            ],
                                            style={
                                                "display": "flex",
                                                "justify-content": "flex-end",
                                            },
                                        ),
                                    ],
                                ),
                                dmc.Space(h=20),
                                dmc.Button(
                                    "Clear all annotations",
                                    id="clear-all",
                                    variant="outline",
                                    style={"width": "100%"},
                                ),
                                dmc.Space(h=3),
                                dmc.Button(
                                    "Save and export",
                                    id="open-data-management-modal-button",
                                    variant="outline",
                                    color="#00313C",
                                    style={"width": "100%"},
                                ),
                                dmc.Modal(
                                    title="Data Management",
                                    id="data-management-modal",
                                    centered=True,
                                    zIndex=10000,
                                    children=[
                                        dmc.Divider(
                                            variant="solid",
                                            label="Save data",
                                            labelPosition="center",
                                        ),
                                        dmc.Center(
                                            dmc.Button(
                                                "Save to server",
                                                id="save-annotations",
                                                variant="light",
                                                style={
                                                    "width": "160px",
                                                    "margin": "5px",
                                                },
                                            ),
                                        ),
                                        dmc.Text(
                                            id="data-modal-save-status",
                                            align="center",
                                            italic=True,
                                        ),
                                        dmc.Space(h=20),
                                        dmc.Divider(
                                            variant="solid",
                                            label="Load data",
                                            labelPosition="center",
                                        ),
                                        dmc.Space(h=10),
                                        dmc.Center(
                                            dmc.HoverCard(
                                                withArrow=True,
                                                shadow="md",
                                                children=[
                                                    dmc.HoverCardTarget(
                                                        dmc.Button(
                                                            "From server",
                                                            variant="light",
                                                            style={
                                                                "width": "160px",
                                                                "margin": "5px",
                                                            },
                                                        )
                                                    ),
                                                    dmc.HoverCardDropdown(
                                                        id="load-annotations-server-container",
                                                    ),
                                                ],
                                            ),
                                        ),
                                        dmc.Space(h=20),
                                        dmc.Divider(
                                            variant="solid",
                                            labelPosition="center",
                                        ),
                                        dmc.Space(h=10),
                                        dmc.Center(
                                            dmc.Button(
                                                "Export annotation",
                                                id="export-annotation",
                                                variant="light",
                                                style={
                                                    "width": "160px",
                                                    "margin": "5px",
                                                },
                                            ),
                                        ),
                                    ],
                                ),
                                dmc.Space(h=20),
                            ],
                        ),
                        _accordion_item(
                            "Model configuration",
                            "carbon:ibm-watson-machine-learning",
                            "run-model",
                            id="model-configuration",
                            children=[
                                dmc.Button(
                                    "Run model",
                                    id="run-model",
                                    variant="light",
                                    style={"width": "160px", "margin": "5px"},
                                ),
                                html.Div(id="output-details"),
                                html.Div(
                                    id="overlay-switch-container",
                                    children=[
                                        dmc.Switch(
                                            id="show-result-overlay",
                                            size="sm",
                                            radius="lg",
                                            color="gray",
                                            label="View segmentation overlay",
                                            checked=False,
                                            disabled=True,
                                            styles={
                                                "trackLabel": {"cursor": "pointer"}
                                            },
                                        ),
                                    ],
                                    loading=False,
                                ),
                                dmc.Select(
                                    id="result-selector",
                                    placeholder="Select an ML result...",
                                ),
                                dmc.Slider(
                                    id="seg-result-opacity-slider",
                                    value=50,
                                    min=0,
                                    max=100,
                                    step=1,
                                    color="gray",
                                    size="sm",
                                    style={"width": "225px"},
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
    )


def drawer_section(children):
    """
    This components creates an affix button that opens a drawer with the given children.
    Drawer is set to have height and width of fit-content, meaning it won't be full height.
    """
    return html.Div(
        [
            dmc.Affix(
                dmc.Button(
                    [
                        DashIconify(
                            icon="circum:settings",
                            height=25,
                            style={"cursor": "pointer"},
                        ),
                        dmc.Text("Controls", size="sm"),
                    ],
                    id="drawer-controls-open-button",
                    size="lg",
                    radius="sm",
                    compact=True,
                    variant="outline",
                    color="gray",
                ),
                position={"left": "25px", "top": "25px"},
            ),
            dmc.Drawer(
                title=dmc.Text("ML Exchange Image Segmentation", weight=700),
                id="drawer-controls",
                padding="md",
                transition="fade",
                transitionDuration=500,
                shadow="md",
                withOverlay=False,
                position="left",
                zIndex=10000,
                styles={
                    "drawer": {
                        "width": "fit-content",
                        "height": "fit-content",
                        "max-height": "100%",
                        "overflow-y": "auto",
                        "margin": "0px",
                    },
                    "root": {
                        "opacity": "0.95",
                    },
                },
                children=children,
                opened=True,
            ),
            dcc.Store(
                id="annotation-store",
                data={
                    "dragmode": "drawopenpath",
                    "visible": True,
                    "view": {},
                    "active_img_shape": [],
                    "image_center_coor": {},
                },
            ),
            create_reset_view_affix(),
            create_info_card_affix(),
            dmc.NotificationsProvider(html.Div(id="notifications-container")),
            dcc.Download(id="export-annotation-metadata"),
            dcc.Download(id="export-annotation-mask"),
            dcc.Store(id="project-data"),
            dcc.Store(id="submitted-job-id"),
            dcc.Interval(
                id="model-check", interval=5000
            ),  # TODO: May want to increase frequency
            html.Div(id="dummy-output"),
            EventListener(
                events=[
                    {
                        "event": "keydown",
                        "props": ["key", "ctrlKey", "ctrlKey"],
                    }
                ],
                id="keybind-event-listener",
            ),
        ]
    )


def create_keybind_row(keys, text):
    keybinds = []
    for key in keys:
        keybinds.append(dmc.Kbd(key))
        keybinds.append(" + ")
    keybinds.pop()
    return dmc.Group(
        position="apart",
        children=[html.Div(keybinds), dmc.Text(text, size="sm")],
    )


def create_reset_view_affix():
    return dmc.Affix(
        position={"bottom": 60, "right": 20},
        zIndex=9999999,
        children=_tooltip(
            text="Center the image",
            children=dmc.ActionIcon(
                DashIconify(icon="carbon:center-square"),
                id="reset-view",
                size="lg",
                radius="lg",
                variant="filled",
                mb=10,
            ),
        ),
    )


def create_info_card_affix():
    return dmc.Affix(
        position={"bottom": 20, "right": 20},
        zIndex=9999999,
        children=dmc.HoverCard(
            shadow="md",
            position="top-start",
            children=[
                dmc.HoverCardTarget(
                    dmc.ActionIcon(
                        DashIconify(icon="entypo:info"),
                        size="lg",
                        radius="lg",
                        variant="filled",
                        mb=10,
                    ),
                ),
                dmc.HoverCardDropdown(
                    style={"marginRight": "20px"},
                    children=[
                        dmc.Text(
                            "Shortcuts",
                            size="lg",
                            weight=700,
                        ),
                        dmc.Stack(
                            [
                                dmc.Divider(variant="solid", color="gray"),
                                create_keybind_row(
                                    "→",
                                    "Next slice",
                                ),
                                create_keybind_row(
                                    "←",
                                    "Previous slice",
                                ),
                                dmc.Divider(variant="solid", color="gray"),
                                create_keybind_row(
                                    KEYBINDS["open-freeform"].upper(),
                                    "Open Freeform",
                                ),
                                create_keybind_row(
                                    KEYBINDS["closed-freeform"].upper(),
                                    "Closed Freeform",
                                ),
                                create_keybind_row(
                                    KEYBINDS["line"].upper(),
                                    "Line Annotation Mode",
                                ),
                                create_keybind_row(
                                    KEYBINDS["circle"].upper(),
                                    "Circle Annotation Mode",
                                ),
                                create_keybind_row(
                                    KEYBINDS["rectangle"].upper(),
                                    "Rectangle Annotation Mode",
                                ),
                                dmc.Divider(variant="solid", color="gray"),
                                create_keybind_row(
                                    KEYBINDS["pan-and-zoom"].upper(),
                                    "Pan and Zoom Mode",
                                ),
                                create_keybind_row(
                                    KEYBINDS["erase"].upper(),
                                    "Erase Annotation Mode",
                                ),
                                dmc.Divider(variant="solid", color="gray"),
                                create_keybind_row(
                                    ["1-9"],
                                    "Select annotation class 1-9",
                                ),
                            ],
                            p=0,
                        ),
                    ],
                ),
            ],
        ),
    )
