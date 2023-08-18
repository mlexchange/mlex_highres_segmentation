import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from utils import data_utils
from constants import ANNOT_ICONS, KEYBINDS
import random
from dash_extensions import EventListener


def _accordion_item(title, icon, value, children, id):
    return dmc.AccordionItem(
        [
            dmc.AccordionControl(
                title,
                icon=DashIconify(
                    icon=icon,
                    color=dmc.theme.DEFAULT_COLORS["blue"][6],
                    width=20,
                ),
            ),
            dmc.LoadingOverlay(
                dmc.AccordionPanel(children=children, id=id),
                loaderProps={"size": 0},
                overlayOpacity=0.4,
            ),
        ],
        value=value,
    )


def layout():
    DATA_OPTIONS = data_utils.get_data_project_names()
    return drawer_section(
        dmc.Stack(
            style={"width": "400px"},
            children=[
                dmc.AccordionMultiple(
                    chevron=DashIconify(icon="ant-design:plus-outlined"),
                    disableChevronRotation=True,
                    value=["data-select", "image-transformations", "annotations"],
                    children=[
                        _accordion_item(
                            "Data selection",
                            "majesticons:data-line",
                            "data-select",
                            id="data-selection-controls",
                            children=[
                                dmc.Text("Image"),
                                dmc.Select(
                                    id="project-name-src",
                                    data=DATA_OPTIONS,
                                    value=DATA_OPTIONS[0] if DATA_OPTIONS else None,
                                    placeholder="Select an image to view...",
                                ),
                                dmc.Space(h=20),
                                dmc.Grid(
                                    id="image-slice-selection-parent",
                                    children=[
                                        dmc.Col(
                                            dmc.Tooltip(
                                                label="Previous image",
                                                children=dmc.ActionIcon(
                                                    DashIconify(
                                                        icon="ooui:previous-ltr",
                                                        width=20,
                                                    ),
                                                    variant="filled",
                                                    id="image-selection-previous",
                                                    mt=15,
                                                ),
                                            ),
                                            span=1,
                                        ),
                                        dmc.Col(
                                            [
                                                dmc.Text(
                                                    "Selected image: 1",
                                                    align="center",
                                                    id="image-selection-text",
                                                ),
                                                dmc.Slider(
                                                    min=1,
                                                    max=1000,
                                                    step=1,
                                                    value=25,
                                                    id="image-selection-slider",
                                                ),
                                            ],
                                            span="auto",
                                        ),
                                        dmc.Col(
                                            dmc.Tooltip(
                                                label="Next image",
                                                children=dmc.ActionIcon(
                                                    DashIconify(
                                                        icon="ooui:previous-rtl",
                                                        width=20,
                                                    ),
                                                    variant="filled",
                                                    id="image-selection-next",
                                                    mt=15,
                                                ),
                                            ),
                                            span=1,
                                        ),
                                    ],
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
                                    dmc.Text("Brightness", size="sm"),
                                    dmc.Slider(
                                        id=f"figure-brightness",
                                        value=100,
                                        min=0,
                                        max=255,
                                        step=1,
                                        color="gray",
                                        size="sm",
                                    ),
                                    dmc.Space(h=5),
                                    dmc.Text("Contrast", size="sm"),
                                    dmc.Slider(
                                        id=f"figure-contrast",
                                        value=100,
                                        min=0,
                                        max=255,
                                        step=1,
                                        color="gray",
                                        size="sm",
                                    ),
                                    dmc.Space(h=10),
                                    dmc.ActionIcon(
                                        dmc.Tooltip(
                                            label="Reset filters",
                                            children=[
                                                DashIconify(
                                                    icon="fluent:arrow-reset-32-regular",
                                                    width=20,
                                                ),
                                            ],
                                        ),
                                        size="lg",
                                        variant="filled",
                                        id="filters-reset",
                                        n_clicks=0,
                                        mb=10,
                                        ml="auto",
                                        style={"margin": "auto"},
                                    ),
                                ]
                            ),
                        ),
                        _accordion_item(
                            "Annotation tools",
                            "mdi:paintbrush-outline",
                            "annotations",
                            id="annotations-controls",
                            children=[
                                dmc.Center(
                                    dmc.Switch(
                                        id="view-annotations",
                                        size="sm",
                                        radius="lg",
                                        color="gray",
                                        label="View annotation layer",
                                        checked=True,
                                        styles={"trackLabel": {"cursor": "pointer"}},
                                    )
                                ),
                                dmc.Space(h=20),
                                dmc.Text("Annotation mode", size="sm"),
                                html.Div(
                                    children=[
                                        dmc.Tooltip(
                                            dmc.ActionIcon(
                                                id="open-freeform",
                                                variant="outline",
                                                color="gray",
                                                children=DashIconify(
                                                    icon=ANNOT_ICONS["open-freeform"]
                                                ),
                                                style={"border": "3px solid black"},
                                            ),
                                            label="Open Freeform: draw any open shape",
                                            multiline=True,
                                        ),
                                        dmc.Tooltip(
                                            dmc.ActionIcon(
                                                id="closed-freeform",
                                                variant="outline",
                                                color="gray",
                                                children=DashIconify(
                                                    icon=ANNOT_ICONS["closed-freeform"]
                                                ),
                                            ),
                                            label="Closed Freeform: draw a shape that will auto-complete",
                                            multiline=True,
                                        ),
                                        dmc.Tooltip(
                                            dmc.ActionIcon(
                                                id="line",
                                                variant="outline",
                                                color="gray",
                                                children=DashIconify(icon="ci:line-l"),
                                            ),
                                            label="Line: draw a straight line",
                                            multiline=True,
                                        ),
                                        dmc.Tooltip(
                                            dmc.ActionIcon(
                                                id="circle",
                                                variant="outline",
                                                color="gray",
                                                children=DashIconify(
                                                    icon=ANNOT_ICONS["circle"]
                                                ),
                                            ),
                                            label="Circle: create a filled circle",
                                            multiline=True,
                                        ),
                                        dmc.Tooltip(
                                            dmc.ActionIcon(
                                                id="rectangle",
                                                variant="outline",
                                                color="gray",
                                                children=DashIconify(
                                                    icon=ANNOT_ICONS["rectangle"]
                                                ),
                                            ),
                                            label="Rectangle: create a filled rectangle",
                                            multiline=True,
                                        ),
                                        dmc.Tooltip(
                                            dmc.ActionIcon(
                                                id="eraser",
                                                variant="outline",
                                                color="gray",
                                                children=DashIconify(
                                                    icon=ANNOT_ICONS["eraser"]
                                                ),
                                            ),
                                            label="Eraser: click on the shape to erase then click this button to delete the selected shape",
                                            multiline=True,
                                        ),
                                        dmc.Tooltip(
                                            dmc.ActionIcon(
                                                id="delete-all",
                                                variant="outline",
                                                color="gray",
                                                children=DashIconify(
                                                    icon=ANNOT_ICONS["delete-all"]
                                                ),
                                            ),
                                            label="Clear All Annotations",
                                            multiline=True,
                                        ),
                                        dmc.Tooltip(
                                            dmc.ActionIcon(
                                                id="pan-and-zoom",
                                                variant="outline",
                                                color="gray",
                                                children=DashIconify(
                                                    icon=ANNOT_ICONS["pan-and-zoom"]
                                                ),
                                            ),
                                            label="Stop Drawing: pan, zoom, select annotations and edit them using the nodes",
                                            multiline=True,
                                        ),
                                    ],
                                    className="flex-row",
                                    style={"justify-content": "space-evenly"},
                                ),
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
                                                    "Cancel", id="modal-cancel-button"
                                                ),
                                                dmc.Button(
                                                    "Continue",
                                                    color="red",
                                                    variant="outline",
                                                    id="modal-delete-button",
                                                ),
                                            ],
                                            position="right",
                                        ),
                                    ],
                                ),
                                dmc.Space(h=20),
                                dmc.Text("Paintbrush size", size="sm"),
                                dmc.Slider(
                                    id="paintbrush-width",
                                    value=5,
                                    min=1,
                                    max=20,
                                    step=1,
                                    color="gray",
                                    size="sm",
                                ),
                                dmc.Space(h=20),
                                dmc.Text("Annotation class", size="sm"),
                                html.Div(
                                    id="annotation-class-selection",
                                    children=[
                                        dmc.ActionIcon(
                                            id={
                                                "type": "annotation-color",
                                                "index": "rgb(249,82,82)",
                                            },
                                            w=30,
                                            variant="filled",
                                            style={
                                                "background-color": "rgb(249,82,82)",
                                                "border": "3px solid black",
                                                "width": "fit-content",
                                                "padding": "5px",
                                                "margin-right": "10px",
                                            },
                                            children="1",
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "flex-wrap": "wrap",
                                        "justify-content": "space-evenly",
                                    },
                                ),
                                dmc.Space(h=10),
                                dmc.Group(
                                    grow=True,
                                    children=[
                                        dmc.Button(
                                            id="generate-annotation-class",
                                            children="Generate Class",
                                            variant="outline",
                                            leftIcon=DashIconify(
                                                icon="ic:baseline-plus"
                                            ),
                                        ),
                                        dmc.Button(
                                            id="edit-annotation-class",
                                            children="Edit Class",
                                            variant="outline",
                                            leftIcon=DashIconify(icon="uil:edit"),
                                        ),
                                    ],
                                ),
                                dmc.Space(h=10),
                                dmc.Group(
                                    grow=True,
                                    children=[
                                        dmc.Button(
                                            id="hide-annotation-class",
                                            children="Hide/Show Classes",
                                            variant="outline",
                                            leftIcon=DashIconify(icon="mdi:hide"),
                                        ),
                                        dmc.Button(
                                            id="delete-annotation-class",
                                            children="Delete Classes",
                                            variant="outline",
                                            leftIcon=DashIconify(
                                                icon="octicon:trash-24"
                                            ),
                                        ),
                                    ],
                                ),
                                dmc.Modal(
                                    id="generate-annotation-class-modal",
                                    title="Generate a Custom Annotation Class",
                                    children=[
                                        dmc.Center(
                                            dmc.ColorPicker(
                                                id="annotation-class-colorpicker",
                                                format="rgb",
                                            ),
                                        ),
                                        dmc.Space(h=10),
                                        dmc.Center(
                                            dmc.TextInput(
                                                id="annotation-class-label",
                                                placeholder="Annotation Class Label",
                                            ),
                                        ),
                                        dmc.Space(h=10),
                                        dmc.Center(
                                            dmc.Button(
                                                id="create-annotation-class",
                                                children="Create Annotation Class",
                                                variant="light",
                                            ),
                                        ),
                                        html.Div(id="bad-label-color"),
                                    ],
                                ),
                                dmc.Modal(
                                    id="edit-annotation-class-modal",
                                    title="Edit a Custom Annotation Class",
                                    children=[
                                        dmc.Text("Select a generated class to edit:"),
                                        dmc.Select(
                                            id="current-annotation-classes-edit"
                                        ),
                                        dmc.Space(h=10),
                                        dmc.Center(
                                            dmc.TextInput(
                                                id="annotation-class-label-edit",
                                                placeholder="New Class Label",
                                            ),
                                        ),
                                        dmc.Space(h=10),
                                        dmc.Center(
                                            dmc.Button(
                                                id="relabel-annotation-class",
                                                children="Edit Annotation Class",
                                                variant="light",
                                            ),
                                        ),
                                        html.Div(id="bad-label"),
                                    ],
                                ),
                                dmc.Modal(
                                    id="hide-annotation-class-modal",
                                    title="Hide/Show Annotation Classes",
                                    children=[
                                        dmc.Text("Select annotation classes to hide:"),
                                        html.Div(
                                            id="current-annotation-classes-hide",
                                            style={
                                                "display": "flex",
                                                "flex-wrap": "wrap",
                                                "justify-content": "space-evenly",
                                            },
                                        ),
                                        dmc.Space(h=10),
                                        dmc.Center(
                                            dmc.Button(
                                                id="conceal-annotation-class",
                                                children="Apply Changes",
                                                variant="light",
                                            ),
                                        ),
                                        dmc.Center(
                                            dmc.Text(
                                                "No classes selected",
                                                color="red",
                                                id="at-least-one-hide",
                                            ),
                                        ),
                                    ],
                                ),
                                dmc.Modal(
                                    id="delete-annotation-class-modal",
                                    title="Delete Custom Annotation Class(es)",
                                    children=[
                                        dmc.Text(
                                            "Select all generated classes to remove:"
                                        ),
                                        html.Div(
                                            id="current-annotation-classes",
                                            style={
                                                "display": "flex",
                                                "flex-wrap": "wrap",
                                                "justify-content": "space-evenly",
                                            },
                                        ),
                                        dmc.Space(h=10),
                                        dmc.Center(
                                            dmc.Text(
                                                "NOTE: Deleting a class will delete all annotations associated with that class!",
                                                color="red",
                                            )
                                        ),
                                        dmc.Center(
                                            [
                                                dmc.Button(
                                                    id="remove-annotation-class",
                                                    children="Delete Selected Class(es)",
                                                    variant="light",
                                                ),
                                            ]
                                        ),
                                        dmc.Center(
                                            dmc.Text(
                                                "There must be at least one annotation class!",
                                                color="red",
                                                id="at-least-one",
                                            ),
                                        ),
                                    ],
                                ),
                                dmc.Space(h=20),
                                dmc.Center(
                                    dmc.Button(
                                        "Save/Load/Export",
                                        id="open-data-management-modal-button",
                                        variant="light",
                                        style={"width": "160px", "margin": "5px"},
                                    ),
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
                                html.Div(id="output-placeholder"),
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
                    "annotations": {},
                    "view": {},
                    "active_img_shape": [],
                    # TODO: Hard-coding default annotation class
                    "label_mapping": [
                        {
                            "color": "rgb(249,82,82)",
                            "label": "1",
                            "id": "1",
                        }
                    ],
                    "classes_shown": {},
                    "classes_hidden": {},
                },
            ),
            create_info_card_affix(),
            dmc.NotificationsProvider(html.Div(id="notifications-container")),
            dcc.Download(id="export-annotation-metadata"),
            dcc.Download(id="export-annotation-mask"),
            dcc.Store(id="project-data"),
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
                                create_keybind_row(
                                    KEYBINDS["delete-all"].upper(),
                                    "Delete all annotations",
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


def class_action_icon(class_color, class_label, label_color):
    """
    This component creates an action icon for the given annotation class.
    """
    style = {
        "background-color": class_color,
        "width": "fit-content",
        "border": "1px solid black",
        "color": label_color,
        "padding": "5px",
        "margin-right": "10px",
    }
    return dmc.ActionIcon(
        id={"type": "annotation-color", "index": class_color},
        w=30,
        variant="filled",
        style=style,
        children=class_label,
    )
