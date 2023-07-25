import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from utils import data_utils

COMPONENT_STYLE = {
    "width": "400px",
    "height": "calc(100vh - 40px)",
    "padding": "10px",
    "borderRadius": "5px",
    "border": "1px solid rgb(222, 226, 230)",
    "overflowY": "auto",
}
DEFAULT_ANNOTATION_CLASS = "red"


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
    return dmc.Stack(
        style=COMPONENT_STYLE,
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
                            dmc.Group(
                                spacing="xs",
                                grow=True,
                                children=[
                                    dmc.Tooltip(
                                        dmc.ActionIcon(
                                            id="open-freeform",
                                            variant="outline",
                                            color="gray",
                                            children=DashIconify(icon="mdi:draw"),
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
                                                icon="fluent:draw-shape-20-regular"
                                            ),
                                        ),
                                        label="Closed Freeform: draw a shape that will auto-complete",
                                        multiline=True,
                                    ),
                                    dmc.Tooltip(
                                        dmc.ActionIcon(
                                            id="circle",
                                            variant="outline",
                                            color="gray",
                                            children=DashIconify(
                                                icon="gg:shape-circle"
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
                                                icon="gg:shape-square"
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
                                            children=DashIconify(icon="ph:eraser"),
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
                                                icon="octicon:trash-24"
                                            ),
                                        ),
                                        label="Clear All Annotations",
                                        multiline=True,
                                    ),
                                    dmc.Tooltip(
                                        dmc.ActionIcon(
                                            id="drawing-off",
                                            variant="outline",
                                            color="gray",
                                            children=DashIconify(icon="el:off"),
                                        ),
                                        label="Stop Drawing: pan, zoom, select annotations and edit them using the nodes",
                                        multiline=True,
                                    ),
                                ],
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
                            dmc.Group(
                                spacing="xs",
                                grow=True,
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
                                        },
                                        children="1",
                                    ),
                                ],
                            ),
                            dmc.Space(h=5),
                            html.Div(
                                [
                                    dmc.Button(
                                        id="generate-annotation-class",
                                        children="Generate Class",
                                        variant="outline",
                                        leftIcon=DashIconify(icon="ic:baseline-plus"),
                                    ),
                                    dmc.Button(
                                        id="delete-annotation-class",
                                        children="Delete Class",
                                        variant="outline",
                                        style={"margin-left": "auto"},
                                        leftIcon=DashIconify(icon="octicon:trash-24"),
                                    ),
                                ],
                                className="flex-row",
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
                                id="delete-annotation-class-modal",
                                title="Delete Custom Annotation Class(es)",
                                children=[
                                    dmc.Text("Select all generated classes to remove:"),
                                    dmc.Group(
                                        spacing="xs",
                                        grow=True,
                                        id="current-annotation-classes",
                                    ),
                                    dmc.Space(h=10),
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
                                    "Save annotation",
                                    variant="light",
                                    style={"width": "160px", "margin": "5px"},
                                )
                            ),
                            dmc.Center(
                                dmc.Button(
                                    "Export annotation",
                                    variant="light",
                                    style={"width": "160px", "margin": "5px"},
                                )
                            ),
                            dmc.Space(h=20),
                        ],
                    ),
                ],
            ),
            dcc.Store(
                id="annotation-store",
                data={
                    "dragmode": "drawopenpath",
                    "visible": True,
                    "annotations": {},
                    "view": {},
                    "image_size": [],
                    "classes": {1: "1"},
                },
            ),
            dcc.Store(id="project-data"),
            html.Div(id="dummy-output"),
        ],
    )
