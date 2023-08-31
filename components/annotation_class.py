import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify


def annotation_class_item(class_color, class_label):
    color = class_color
    class_color = color.replace("rgb", "rgba")
    class_color_transparent = class_color[:-1] + ",0.5)"
    return html.Div(
        [  # This store will contain all the meta data for an individual annotation class
            dcc.Store(
                id={
                    "type": "annotation-class-store",
                    "index": color,
                },
                data={
                    "annotations": {},
                    "color": color,
                    "id": None,
                    "label": class_label,
                    "class_visible": True,
                    "deleted": False,
                },
            ),
            html.Div(
                [
                    html.Div(
                        style={
                            "width": "25px",
                            "height": "25px",
                            "background-color": class_color_transparent,
                            "margin": "5px",
                            "borderRadius": "3px",
                            "border": f"2px solid {color}",
                        },
                    ),
                    html.Div(
                        class_label,
                        id={
                            "type": "annotation-class-label",
                            "index": color,
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
                            "index": color,
                        },
                        variant="subtle",
                        color="gray",
                        children=DashIconify(icon="mdi:hide"),
                        size="lg",
                    ),
                    dmc.ActionIcon(
                        id={
                            "type": "edit-annotation-class",
                            "index": color,
                        },
                        variant="subtle",
                        color="gray",
                        children=DashIconify(icon="uil:edit"),
                        size="lg",
                    ),
                    dmc.ActionIcon(
                        id={
                            "type": "delete-annotation-class",
                            "index": color,
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
            dmc.Modal(
                id={"type": "edit-annotation-class-modal", "index": color},
                title="Edit a Custom Annotation Class",
                children=[
                    dmc.Center(
                        dmc.TextInput(
                            id={
                                "type": "edit-annotation-class-text-input",
                                "index": color,
                            },
                            placeholder="New Class Label",
                        ),
                    ),
                    dmc.Space(h=10),
                    dmc.Center(
                        dmc.Button(
                            id={
                                "type": "relabel-annotation-class-btn",
                                "index": color,
                            },
                            children="Edit Annotation Class",
                            variant="light",
                        ),
                    ),
                    html.Div(id={"type": "bad-edit-label", "index": color}),
                ],
            ),
            dmc.Modal(
                id={"type": "delete-annotation-class-modal", "index": color},
                title="Delete Custom Annotation Class",
                children=[
                    dmc.Center(
                        dmc.Text(
                            "NOTE: Deleting a class will delete all annotations associated with that class!",
                            color="red",
                        )
                    ),
                    dmc.Center(
                        [
                            dmc.Button(
                                id={
                                    "type": "remove-annotation-class-btn",
                                    "index": color,
                                },
                                children="Delete Selected Class",
                                variant="light",
                            ),
                        ]
                    ),
                    dmc.Center(
                        dmc.Text(
                            id={
                                "type": "delete-last-class-warning",
                                "index": color,
                            }
                        )
                    ),
                ],
            ),
        ],
        style={
            "border": "1px solid #EAECEF",
            "borderRadius": "3px",
            "marginBottom": "4px",
            "display": "flex",
            "justifyContent": "space-between",
        },
        id={"type": "annotation-class", "index": color},
    )
