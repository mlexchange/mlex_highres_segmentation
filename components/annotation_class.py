import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify


# This fucntion creates the action icons needed for an annoation class: specifically hide/show, edit and delete actions
def get_action_icon(id, color, icon):
    return dmc.ActionIcon(
        id={
            "type": id,
            "index": color,
        },
        variant="subtle",
        color="gray",
        children=DashIconify(icon=icon),
        size="lg",
    )


# This function generates a class component with all its buttons (hide/show, edit, delete)
# The class color is used as an ID to identify a class (as all class colors are unique and cannot be modified)
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
                    "label": class_label,
                    "is_visible": True,
                },
            ),
            # These stores are solely responsible for triggereing a callback when a class is deleted or shown/hidden
            dcc.Store(id={"type": "deleted-class-store", "index": color}),
            dcc.Store(
                id={"type": "hide-show-class-store", "index": color},
                data={"is_visible": True},
            ),
            html.Div(
                [
                    # colored box to represent the color of an annotation class
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
                    get_action_icon("hide-annotation-class", color, "mdi:eye"),
                    get_action_icon("edit-annotation-class", color, "uil:edit"),
                    get_action_icon(
                        "delete-annotation-class", color, "octicon:trash-24"
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "flex-row",
                    "align-items": "center",
                    "padding": "3px",
                },
            ),
            dmc.Modal(
                id={"type": "edit-annotation-class-modal", "index": color},
                title="Edit a Custom Annotation Class",
                children=[
                    dmc.TextInput(
                        id={
                            "type": "edit-annotation-class-text-input",
                            "index": color,
                        },
                        placeholder="New class name...",
                        style={"width": "70%"},
                    ),
                    html.Div(
                        id={"type": "bad-edit-label", "index": color},
                        style={"color": "red", "fontSize": "12px", "padding": "3px"},
                    ),
                    dmc.Space(h=25),
                    html.Div(
                        dmc.Button(
                            id={
                                "type": "relabel-annotation-class-btn",
                                "index": color,
                            },
                            children="Save",
                        ),
                        style={
                            "display": "flex",
                            "justify-content": "flex-end",
                        },
                    ),
                ],
            ),
            dmc.Modal(
                id={"type": "delete-annotation-class-modal", "index": color},
                children=[
                    dmc.Center(
                        dmc.Text(
                            "This action will permanently clear all annotations from this class. Are you sure you want to proceed?",
                        )
                    ),
                    dmc.Space(h=10),
                    html.Div(
                        [
                            dmc.Button(
                                id={
                                    "type": "modal-cancel-delete-class-btn",
                                    "index": color,
                                },
                                children="Cancel",
                            ),
                            dmc.Space(w=10),
                            dmc.Button(
                                id={
                                    "type": "modal-continue-delete-class-btn",
                                    "index": color,
                                },
                                children="Confirm",
                                variant="outline",
                                color="red",
                            ),
                        ],
                        style={
                            "display": "flex",
                            "justify-content": "flex-end",
                        },
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
        className="annotation-class",
        id={"type": "annotation-class", "index": color},
    )
