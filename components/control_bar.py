import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from utils import data_utils
from constants import ANNOT_ICONS, KEYBINDS
from dash_extensions import EventListener


def _tooltip(text, children):
    return dmc.Tooltip(
        label=text, withArrow=True, position="top", color="#464646", children=children
    )


def _control_item(title, title_id, item):
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


def _accordion_item(title, icon, value, children, id):
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
            dmc.LoadingOverlay(
                dmc.AccordionPanel(children=children, id=id),
                loaderProps={"size": 0},
                overlayOpacity=0.4,
            ),
        ],
        value=value,
    )


def annotation_class_item(class_color, class_label):
    border_color = class_color
    class_color = class_color.replace("rgb", "rgba")
    class_color = class_color[:-1] + ",0.5)"
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        style={
                            "width": "25px",
                            "height": "25px",
                            "background-color": class_color,
                            "margin": "5px",
                            "borderRadius": "3px",
                            "border": f"2px solid {border_color}",
                        },
                        id={
                            "type": "annotation-class-color",
                            "index": f"{class_label};{class_color}",
                        },
                    ),
                    html.Div(
                        class_label,
                        id={
                            "type": "annotation-class-label",
                            "index": f"{class_label};{class_color}",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "flex-row",
                    "align-items": "center",
                    "color": "#9EA4AB",
                },
            ),
            html.Div(
                [
                    dmc.ActionIcon(
                        id={
                            "type": "hide-annotation-class",
                            "index": f"{class_label};{class_color}",
                        },
                        variant="subtle",
                        color="gray",
                        children=DashIconify(icon="mdi:hide"),
                        size="lg",
                    ),
                    dmc.ActionIcon(
                        id={
                            "type": "edit-annotation-class",
                            "index": f"{class_label};{class_color}",
                        },
                        variant="subtle",
                        color="gray",
                        children=DashIconify(icon="uil:edit"),
                        size="lg",
                    ),
                    dmc.ActionIcon(
                        id={
                            "type": "delete-annotation-class",
                            "index": f"{class_label};{class_color}",
                        },
                        variant="subtle",
                        color="gray",
                        children=DashIconify(icon="octicon:trash-24"),
                        size="lg",
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "flex-row",
                    "align-items": "center",
                },
            ),
        ],
        style={
            "border": "1px solid #EAECEF",
            "borderRadius": "3px",
            "marginBottom": "4px",
            "display": "flex",
            "justifyContent": "space-between",
        },
        id={"type": "annotation-class", "index": f"{class_label};{class_color}"},
    )


def layout():
    DATA_OPTIONS = data_utils.get_data_project_names()
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
                                dmc.Space(h=5),
                                dmc.Grid(
                                    [
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
                                                dmc.Tooltip(
                                                    dmc.ActionIcon(
                                                        id="delete-all",
                                                        variant="subtle",
                                                        color="gray",
                                                        children=DashIconify(
                                                            icon=ANNOT_ICONS[
                                                                "delete-all"
                                                            ],
                                                            width=20,
                                                        ),
                                                        size="lg",
                                                    ),
                                                    label="Clear All Annotations",
                                                    multiline=True,
                                                ),
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
                                                "width": "275px",
                                                "justify-content": "space-evenly",
                                                "padding": "2.5px",
                                                "border": "1px solid #EAECEF",
                                                "border-radius": "5px",
                                            },
                                        ),
                                        dmc.Switch(
                                            id="view-annotations",
                                            size="xs",
                                            radius="md",
                                            color="gray",
                                            label="View",
                                            checked=True,
                                            styles={
                                                "trackLabel": {"cursor": "pointer"},
                                                "margin": "auto",
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
                                    ),
                                ),
                                dmc.Space(h=20),
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
                                html.Div(
                                    [
                                        dmc.Text(
                                            "Manage classes",
                                            size="sm",
                                            align="right",
                                            color="#9EA4AB",
                                        ),
                                        dmc.Space(h=10),
                                        html.Div(
                                            children=[
                                                annotation_class_item(
                                                    "rgb(22,17,79)", "class 1"
                                                )
                                            ],
                                            id="annotation-class-container",
                                        ),
                                        dmc.Button(
                                            "+ Add new class... ",
                                            id="generate-annotation-class",
                                            variant="outline",
                                            style={"width": "100%"},
                                            className="add-class-btn",
                                        ),
                                        dmc.Space(h=20),
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
                                                "justify-content": "flex-start",
                                            },
                                        ),
                                        dmc.Space(h=10),
                                        dmc.Grid(
                                            justify="space-between",
                                            children=[
                                                # dmc.Button(
                                                #     id="generate-annotation-class",
                                                #     children="Add",
                                                #     variant="subtle",
                                                #     color="gray",
                                                #     style={"width": "85px"},
                                                #     leftIcon=DashIconify(
                                                #         icon="ic:baseline-plus"
                                                #     ),
                                                # ),
                                                dmc.Button(
                                                    id="edit-annotation-class",
                                                    children="Edit",
                                                    variant="subtle",
                                                    color="gray",
                                                    style={"width": "85px"},
                                                    leftIcon=DashIconify(
                                                        icon="uil:edit"
                                                    ),
                                                ),
                                                dmc.Button(
                                                    id="hide-annotation-class",
                                                    children="View",
                                                    variant="subtle",
                                                    color="gray",
                                                    style={"width": "85px"},
                                                    leftIcon=DashIconify(
                                                        icon="mdi:hide"
                                                    ),
                                                ),
                                                dmc.Button(
                                                    id="delete-annotation-class",
                                                    children="Delete",
                                                    variant="subtle",
                                                    color="gray",
                                                    style={"width": "90px"},
                                                    leftIcon=DashIconify(
                                                        icon="octicon:trash-24"
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ],
                                    style={
                                        # "border": "1px solid #EAECEF",
                                        # "borderRadius": "5px",
                                        # "padding": "10px",
                                    },
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
                                                "justify-content": "flex-start",
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
                                                "justify-content": "flex-start",
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
        "backgroundColor": "#EAECEF",
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
