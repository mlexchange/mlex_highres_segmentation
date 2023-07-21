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


def _accordion_item(title, icon, value, children):
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
            dmc.AccordionPanel(children),
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
                                    disabled=True,
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
                                    disabled=True,
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
                                    disabled=True,
                                ),
                            ]
                        ),
                    ),
                    _accordion_item(
                        "Annotation tools",
                        "mdi:paintbrush-outline",
                        "annotations",
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
                                    disabled=True,
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
                                            disabled=True,
                                        ),
                                        label="Open Freeform",
                                    ),
                                    dmc.Tooltip(
                                        dmc.ActionIcon(
                                            id="closed-freeform",
                                            variant="outline",
                                            color="gray",
                                            children=DashIconify(
                                                icon="fluent:draw-shape-20-regular"
                                            ),
                                            disabled=True,
                                        ),
                                        label="Closed Freeform",
                                    ),
                                    dmc.Tooltip(
                                        dmc.ActionIcon(
                                            id="circle",
                                            variant="outline",
                                            color="gray",
                                            children=DashIconify(
                                                icon="gg:shape-circle"
                                            ),
                                            disabled=True,
                                        ),
                                        label="Circle",
                                    ),
                                    dmc.Tooltip(
                                        dmc.ActionIcon(
                                            id="rectangle",
                                            variant="outline",
                                            color="gray",
                                            children=DashIconify(
                                                icon="gg:shape-square"
                                            ),
                                            disabled=True,
                                        ),
                                        label="Rectangle",
                                    ),
                                    dmc.Tooltip(
                                        dmc.ActionIcon(
                                            id="drawing-off",
                                            variant="outline",
                                            color="gray",
                                            children=DashIconify(icon="el:off"),
                                            disabled=True,
                                        ),
                                        label="Stop Drawing",
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
                                disabled=True,
                            ),
                            dmc.Space(h=20),
                            dmc.Text("Annotation class", size="sm"),
                            dmc.Group(
                                spacing="xs",
                                grow=True,
                                id="annotation-class-selection",
                                className=DEFAULT_ANNOTATION_CLASS,
                                children=[
                                    dmc.ActionIcon(
                                        children=(i + 1),
                                        color=color,
                                        variant="filled",
                                        className=f"{color}-icon",
                                        id={"type": "annotation-color", "index": color},
                                        w=30,
                                        disabled=True,
                                    )
                                    for i, color in enumerate(
                                        [
                                            # "gray",
                                            "red",
                                            # "pink",
                                            "grape",
                                            "violet",
                                            # "indigo",
                                            "blue",
                                            # "lime",
                                            "yellow",
                                            # "orange",
                                        ]
                                    )
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
                },
            ),
            dcc.Store(id="project-data"),
            html.Div(id="dummy-output"),
        ],
    )
