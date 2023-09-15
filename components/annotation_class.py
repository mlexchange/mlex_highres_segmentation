import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify


def get_action_icon(type, class_id, icon):
    """
    Returns the action icons needed for an annotations class. Specifically, hide/show,
    edit, and delete actions.
    """
    return dmc.ActionIcon(
        id={
            "type": type,
            "index": class_id,
        },
        variant="subtle",
        color="gray",
        children=DashIconify(icon=icon),
        size="lg",
    )


def annotation_class_item(class_color, class_label, existing_ids, data=None):
    """
    Returns the layout for an annotation class item. Includes all relevant buttons and
    various dcc.Stores that enable functionality with existing pattern-matching callbacks.
    """
    if data:
        class_color = data["color"]
        class_label = data["label"]
        class_id = data["class_id"]
        annotations = data["annotations"]
        is_visible = data["is_visible"]
    else:
        class_id = 1 if not existing_ids else max(existing_ids) + 1
        annotations = {}
        is_visible = True
    class_color_transparent = class_color + "50"

    return html.Div(
        [  # This store will contain all the meta data for an individual annotation class
            dcc.Store(
                id={
                    "type": "annotation-class-store",
                    "index": class_id,
                },
                data={
                    "annotations": annotations,
                    "color": class_color,
                    "label": class_label,
                    "is_visible": is_visible,
                    "class_id": class_id,
                },
            ),
            # These stores are solely responsible for triggereing a callback when a class is deleted or shown/hidden
            dcc.Store(id={"type": "deleted-class-store", "index": class_id}),
            dcc.Store(
                id={"type": "hide-show-class-store", "index": class_id},
                data={"is_visible": True},
            ),
            dcc.Store(
                id={"type": "edit-class-store", "index": class_id},
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
                            "border": f"2px solid {class_color}",
                        },
                        id={
                            "type": "annotation-class-color",
                            "index": class_id,
                        },
                    ),
                    html.Div(
                        class_label,
                        id={
                            "type": "annotation-class-label",
                            "index": class_id,
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
                    get_action_icon("hide-annotation-class", class_id, "mdi:eye"),
                    get_action_icon("edit-annotation-class", class_id, "uil:edit"),
                    get_action_icon(
                        "delete-annotation-class", class_id, "octicon:trash-24"
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
                id={"type": "edit-annotation-class-modal", "index": class_id},
                title="Edit a Custom Annotation Class",
                children=[
                    html.Div(
                        [
                            dbc.Input(
                                type="color",
                                id={
                                    "type": "edit-annotation-class-colorpicker",
                                    "index": class_id,
                                },
                                style={"width": 75, "height": 50},
                            ),
                            dmc.Space(w=25),
                            html.Div(
                                [
                                    dmc.TextInput(
                                        id={
                                            "type": "edit-annotation-class-text-input",
                                            "index": class_id,
                                        },
                                        placeholder="New class label...",
                                    ),
                                    html.Div(
                                        id={
                                            "type": "bad-edit-label",
                                            "index": class_id,
                                        },
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
                            "justify-content": "flex-row",
                            "align-items": "center",
                        },
                    ),
                    html.Div(
                        [
                            dmc.Button(
                                id={
                                    "type": "save-edited-annotation-class-btn",
                                    "index": class_id,
                                },
                                children="Save",
                            ),
                        ],
                        style={
                            "display": "flex",
                            "justify-content": "flex-end",
                        },
                    ),
                ],
            ),
            dmc.Modal(
                id={"type": "delete-annotation-class-modal", "index": class_id},
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
                                    "index": class_id,
                                },
                                children="Cancel",
                            ),
                            dmc.Space(w=10),
                            dmc.Button(
                                id={
                                    "type": "modal-continue-delete-class-btn",
                                    "index": class_id,
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
        id={"type": "annotation-class", "index": class_id},
    )
