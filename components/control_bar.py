import os

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html
from dash_extensions import EventListener
from dash_iconify import DashIconify

from components.annotation_class import annotation_class_item
from components.parameter_items import ControlItem
from constants import ANNOT_ICONS, KEYBINDS
from utils.data_utils import models, tiled_datasets

RESULTS_DIR = os.getenv("RESULTS_DIR", "")


def _tooltip(text, children):
    """
    Returns a customized layout for a tooltip
    """
    return dmc.Tooltip(
        label=text, withArrow=True, position="top", color="#464646", children=children
    )


def _accordion_item(title, icon, value, children, id):
    """
    Returns a customized layout for an accordion item
    """
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
    DATA_OPTIONS = [item for item in tiled_datasets.get_data_project_names()]
    return drawer_section(
        dmc.Stack(
            style={"width": "400px"},
            children=[
                dmc.AccordionMultiple(
                    id="control-accordion",
                    value=["data-select", "image-transformations", "annotations"],
                    children=[
                        _accordion_item(
                            "Data selection",
                            "majesticons:data-line",
                            "data-select",
                            id="data-selection-controls",
                            children=[
                                dmc.Space(h=5),
                                ControlItem(
                                    "Dataset",
                                    "image-selector",
                                    dmc.Grid(
                                        [
                                            dmc.Select(
                                                id="project-name-src",
                                                data=DATA_OPTIONS,
                                                value=(
                                                    DATA_OPTIONS[0]
                                                    if DATA_OPTIONS
                                                    else None
                                                ),
                                                placeholder="Select an image to view...",
                                            ),
                                            dmc.ActionIcon(
                                                _tooltip(
                                                    "Refresh dataset",
                                                    children=[
                                                        DashIconify(
                                                            icon="mdi:refresh-circle",
                                                            width=20,
                                                        ),
                                                    ],
                                                ),
                                                size="xs",
                                                variant="subtle",
                                                id="refresh-tiled",
                                                n_clicks=0,
                                                style={"margin": "auto"},
                                            ),
                                        ],
                                        style={"margin": "0px"},
                                    ),
                                ),
                                dmc.Space(h=25),
                                ControlItem(
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
                                dmc.Space(h=25),
                                ControlItem(
                                    _tooltip(
                                        "Jump to your annotated slices",
                                        "Annotated slices",
                                    ),
                                    "current-annotated-slice",
                                    dmc.Select(
                                        id="annotated-slices-selector",
                                        placeholder="Select a slice to view...",
                                    ),
                                ),
                                dmc.Space(h=10),
                                dmc.Center(
                                    dmc.Loader(
                                        id="image-viewer-loading",
                                        style={"height": "20px", "width": "90px"},
                                        className="hidden",
                                    ),
                                    pt=20,
                                ),
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
                                    ControlItem(
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
                                    ControlItem(
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
                                                    f"Pan and zoom ({KEYBINDS['pan-and-zoom'].upper()})",
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
                                                "justifyContent": "space-evenly",
                                                "padding": "2.5px",
                                                "border": "1px solid #EAECEF",
                                                "borderRadius": "5px",
                                            },
                                        ),
                                        dmc.Space(w=10),
                                        html.Div(
                                            children=[
                                                _tooltip(
                                                    f"Closed freeform ({KEYBINDS['closed-freeform'].upper()})",
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
                                                        style={
                                                            "backgroundColor": "#EAECEF"
                                                        },
                                                        size="lg",
                                                    ),
                                                ),
                                                _tooltip(
                                                    f"Circle ({KEYBINDS['circle'].upper()})",
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
                                                    f"Rectangle ({KEYBINDS['rectangle'].upper()})",
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
                                            ],
                                            className="flex-row",
                                            style={
                                                "width": "301px",
                                                "justifyContent": "space-evenly",
                                                "padding": "2.5px",
                                                "border": "1px solid #EAECEF",
                                                "borderRadius": "5px",
                                            },
                                        ),
                                    ]
                                ),
                                dmc.Space(h=10),
                                dmc.Modal(
                                    title="Warning",
                                    id="delete-all-warning",
                                    children=[
                                        dmc.Text(
                                            "This action will permanently clear all annotations on this image frame."
                                            + " Are you sure you want to proceed?"
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
                                        dcc.Store(
                                            id="current-class-selection", data="#FFA200"
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
                                                "justifyContent": "flex-row",
                                                "alignItems": "center",
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
                                                "justifyContent": "flex-end",
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
                            "Display Qlty 2D Grid Settings",
                            "mdi:grid",
                            "display-grid",
                            id="display-grid-controls",
                            children=[
                                dmc.Text(
                                    "Display Grid Settings",
                                    size="sm",
                                    align="right",
                                    color="#9EA4AB",
                                ),
                                dmc.Space(h=15),
                                dmc.NumberInput(
                                    id="Qlty-window",
                                    label="Qlty Window",
                                    placeholder="Enter window size...",
                                    value=64,
                                    min=0,
                                    max=4096,
                                    step=1,
                                ),
                                dmc.Space(h=15),
                                dmc.NumberInput(
                                    id="Qlty-step",
                                    label="Qlty Step",
                                    placeholder="Enter step size...",
                                    value=32,
                                    min=0,
                                    max=4096,
                                    step=1,
                                ),
                                dmc.Space(h=15),
                                html.Div(
                                    children=[
                                        dmc.Text("Qlty Slider", size="sm", align="center", color="#9EA4AB"),
                                        dmc.Slider(
                                            id="tracer-slider",
                                            value=0,
                                            min=0,
                                            max=1,  
                                            step=1,
                                            color="gray",
                                            size="sm",
                                            style={"width": "225px"},
                                        ),
                                    ],
                                    className="flex-row",
                                    style={
                                        "justifyContent": "space-evenly",
                                        "padding": "2.5px",
                                        "border": "1px solid #EAECEF",
                                        "borderRadius": "5px",
                                    },
                                ),                           
                                dmc.Space(h=20)
                            ],
                        ),
                        _accordion_item(
                            "Model configuration",
                            "carbon:ibm-watson-machine-learning",
                            "run-model",
                            id="model-configuration",
                            children=[
                                ControlItem(
                                    "Model",
                                    "model-selector",
                                    dmc.Select(
                                        id="model-list",
                                        data=models.modelname_list,
                                        value=(
                                            models.modelname_list[0]
                                            if models.modelname_list[0]
                                            else None
                                        ),
                                        placeholder="Select a model...",
                                    ),
                                ),
                                dmc.Space(h=25),
                                ControlItem(
                                    "Model Info",
                                    "model-info",
                                    dmc.Anchor(
                                        dmc.Image(
                                            src="/assets/dlsia.png",
                                            alt="dlsia-logo",
                                            width=150,
                                        ),
                                        id="dlsia-reference",
                                        href="https://dlsia.readthedocs.io/en/latest/",
                                        target="_blank",
                                        size="sm",
                                    ),
                                ),
                                html.Div(id="model-parameters"),
                                dcc.Store(id="model-parameter-values", data={}),
                                dmc.Space(h=25),
                                ControlItem(
                                    "Name",
                                    "job-name-input",
                                    dmc.TextInput(
                                        placeholder="Name your job...",
                                        id="job-name",
                                    ),
                                ),
                                dmc.Space(h=10),
                                dmc.Button(
                                    "Train",
                                    id="run-train",
                                    variant="light",
                                    style={"width": "100%", "margin": "5px"},
                                ),
                                dmc.Space(h=10),
                                ControlItem(
                                    "Train Jobs",
                                    "selected-train-job",
                                    dmc.Select(
                                        placeholder="Select a job...",
                                        id="train-job-selector",
                                    ),
                                ),
                                dmc.Space(h=25),
                                # Maybe add icon: fluent:window-new-20-filled
                                ControlItem(
                                    "Training Stats",
                                    "dvc-training-stats",
                                    dmc.Anchor(
                                        dmc.Text("Open in new window"),
                                        id="dvc-training-stats-link",
                                        href="",
                                        target="_blank",
                                        size="sm",
                                    ),
                                ),
                                dmc.Space(h=10),
                                dmc.Button(
                                    "Inference",
                                    id="run-inference",
                                    variant="light",
                                    style={"width": "100%", "margin": "5px"},
                                ),
                                dmc.Space(h=10),
                                ControlItem(
                                    "Inference Jobs",
                                    "selected-inference-job",
                                    dmc.Select(
                                        placeholder="Select a job...",
                                        id="inference-job-selector",
                                    ),
                                ),
                                dmc.Space(h=25),
                                dmc.Switch(
                                    id="show-result-overlay-toggle",
                                    size="sm",
                                    radius="lg",
                                    color="gray",
                                    label="View segmentation overlay",
                                    checked=False,
                                    disabled=True,
                                    styles={"trackLabel": {"cursor": "pointer"}},
                                ),
                                dcc.Store("seg-results-train-store"),
                                dcc.Store("seg-results-inference-store"),
                                dmc.Space(h=25),
                                ControlItem(
                                    "Opacity",
                                    "",
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
                    "dragmode": "drawclosedpath",
                    "visible": True,
                    "view": {},
                    "active_img_shape": [],
                    "image_center_coor": {},
                },
            ),
            create_reset_view_affix(),
            create_info_card_affix(),
            create_viewfinder_affix(),
            create_infra_state_affix(),
            dmc.NotificationsProvider(html.Div(id="notifications-container")),
            dcc.Download(id="export-annotation-metadata"),
            dcc.Download(id="export-annotation-mask"),
            dcc.Interval(
                id="model-check", interval=5000
            ),  # TODO: May want to increase frequency
            dcc.Interval(id="infra-check", interval=60000),
            dcc.Store(id="infra-state"),
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
        position={"bottom": 100, "right": 20},
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


def create_viewfinder_affix():
    return dmc.Affix(
        position={"top": 10, "right": 10},
        zIndex=9999999,
        children=_tooltip(
            "Toggle viewfinder",
            dmc.Switch(
                size="md",
                radius="lg",
                id="toggle-viewfinder",
                checked=True,
                onLabel="ON",
                offLabel="OFF",
                color="gray",
            ),
        ),
    )


def create_info_card_affix():
    return dmc.Affix(
        position={"bottom": 60, "right": 20},
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
                                    KEYBINDS["closed-freeform"].upper(),
                                    "Closed Freeform",
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
                                dmc.Divider(variant="solid", color="gray"),
                                create_keybind_row(
                                    ["1-9"],
                                    "Select annotation class 1-9",
                                ),
                                dmc.Divider(variant="solid", color="gray"),
                                create_keybind_row(
                                    ["del"],
                                    "Delete an annotation",
                                ),
                            ],
                            p=0,
                        ),
                    ],
                ),
            ],
        ),
    )


def create_infra_state_status(title, icon, id, color):
    return dmc.Group(
        position="left",
        children=[
            DashIconify(icon=icon, width=20, color=color, id=id),
            dmc.Text(title, size="sm"),
        ],
    )


def create_infra_state_details(
    tiled_data_ready=False,
    tiled_masks_ready=False,
    tiled_results_ready=False,
    prefect_ready=False,
    prefect_worker_ready=False,
    timestamp=None,
):
    not_ready_icon = "pajamas:warning-solid"
    not_ready_color = "red"
    ready_icon = "pajamas:check-circle-filled"
    ready_color = "green"

    children = [
        dmc.Text(
            "Infrastructure",
            size="lg",
            weight=700,
        ),
        dmc.Text(
            "----/--/-- --:--:--" if timestamp is None else timestamp,
            size="sm",
            id="infra-state-last-checked",
        ),
        dmc.Stack(
            [
                dmc.Space(h=2),
                dmc.Divider(variant="solid", color="gray"),
                create_infra_state_status(
                    "Tiled (Input)",
                    icon=ready_icon if tiled_data_ready else not_ready_icon,
                    color=ready_color if tiled_data_ready else not_ready_color,
                    id="tiled-data-ready",
                ),
                create_infra_state_status(
                    "Tiled (Masks)",
                    icon=ready_icon if tiled_masks_ready else not_ready_icon,
                    color=ready_color if tiled_masks_ready else not_ready_color,
                    id="tiled-masks-ready",
                ),
                create_infra_state_status(
                    "Tiled (Results)",
                    icon=ready_icon if tiled_results_ready else not_ready_icon,
                    color=ready_color if tiled_results_ready else not_ready_color,
                    id="tiled-results-ready",
                ),
                dmc.Divider(variant="solid", color="gray"),
                create_infra_state_status(
                    "Prefect (Server)",
                    icon=ready_icon if prefect_ready else not_ready_icon,
                    color=ready_color if prefect_ready else not_ready_color,
                    id="prefect-ready",
                ),
                create_infra_state_status(
                    "Prefect (Worker)",
                    icon=ready_icon if prefect_worker_ready else not_ready_icon,
                    color=ready_color if prefect_worker_ready else not_ready_color,
                    id="prefect-worker-ready",
                ),
            ],
            p=0,
        ),
    ]
    return children


def create_infra_state_affix():
    return dmc.Affix(
        position={"bottom": 20, "right": 20},
        zIndex=9999999,
        children=dmc.HoverCard(
            shadow="md",
            position="top-start",
            children=[
                dmc.HoverCardTarget(
                    dmc.ActionIcon(
                        DashIconify(icon="ph:network-fill", id="infra-state-icon"),
                        size="lg",
                        radius="lg",
                        variant="filled",
                        mb=10,
                        id="infra-state-summary",
                    ),
                ),
                dmc.HoverCardDropdown(
                    style={"marginRight": "20px"},
                    id="infra-state-details",
                    children=create_infra_state_details(),
                ),
            ],
        ),
    )
