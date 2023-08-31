import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify


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
                    ),
                    html.Div(
                        class_label,
                        id={
                            "type": "annotation-class-label",
                            "index": border_color,
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
                            "index": border_color,
                        },
                        variant="subtle",
                        color="gray",
                        children=DashIconify(icon="mdi:hide"),
                        size="lg",
                    ),
                    dmc.ActionIcon(
                        id={
                            "type": "edit-annotation-class",
                            "index": border_color,
                        },
                        variant="subtle",
                        color="gray",
                        children=DashIconify(icon="uil:edit"),
                        size="lg",
                    ),
                    dmc.ActionIcon(
                        id={
                            "type": "delete-annotation-class",
                            "index": border_color,
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
        id={"type": "annotation-class", "index": border_color},
    )
