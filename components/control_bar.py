import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from utils import data_utils

COMPONENT_STYLE = {
    "width": "22.5vw",
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
                                dmc.Text("Colormap scalar range", size="sm"),
                                dmc.RangeSlider(
                                    id=f"colormap-scale",
                                    value=[0, 255],
                                    min=0,
                                    max=255,
                                    minRange=0.00001,
                                    step=0.00001,
                                    color="gray",
                                    size="sm",
                                ),
                                dmc.Space(h=5),
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
                                )
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
                            dmc.Space(h=5),
                            dmc.Text("Annotation opacity", size="sm"),
                            dmc.Slider(
                                id="annotation-opacity",
                                value=1,
                                min=0.1,
                                max=1,
                                step=0.1,
                                color="gray",
                                size="sm",
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
            dcc.Store(id="annotation-store", data={}),
        ],
    )
