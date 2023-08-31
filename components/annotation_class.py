import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify


def annotation_class_item(class_color, class_label):
    class_color = class_color.replace("rgb", "rgba")
    class_color_transparent = class_color[:-1] + ",0.5)"
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        style={
                            "width": "25px",
                            "height": "25px",
                            "background-color": class_color_transparent,
                            "margin": "5px",
                            "borderRadius": "3px",
                            "border": f"2px solid {class_color}",
                        },
                    ),
                    html.Div(
                        class_label,
                        id={
                            "type": "annotation-class-label",
                            "index": class_color,
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
                            "index": class_color,
                        },
                        variant="subtle",
                        color="gray",
                        children=DashIconify(icon="mdi:hide"),
                        size="lg",
                    ),
                    dmc.ActionIcon(
                        id={
                            "type": "edit-annotation-class",
                            "index": class_color,
                        },
                        variant="subtle",
                        color="gray",
                        children=DashIconify(icon="uil:edit"),
                        size="lg",
                    ),
                    dmc.ActionIcon(
                        id={
                            "type": "delete-annotation-class",
                            "index": class_color,
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
                id={"type": "edit-annotation-class-modal", "index": class_color},
                title="Edit a Custom Annotation Class",
                children=[
                    dmc.Center(
                        dmc.TextInput(
                            id={
                                "type": "edit-annotation-class-text-input",
                                "index": class_color,
                            },
                            placeholder="New Class Label",
                        ),
                    ),
                    dmc.Space(h=10),
                    dmc.Center(
                        dmc.Button(
                            id={
                                "type": "relabel-annotation-class-btn",
                                "index": class_color,
                            },
                            children="Edit Annotation Class",
                            variant="light",
                        ),
                    ),
                    html.Div(id={"type": "bad-edit-label", "index": class_color}),
                ],
            ),
            dmc.Modal(
                id={"type": "delete-annotation-class-modal", "index": class_color},
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
                                    "index": class_color,
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
                                "index": class_color,
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
        id={"type": "annotation-class", "index": class_color},
    )
