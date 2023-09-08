import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
import uuid


# This fucntion creates the action icons needed for an annoation class: specifically hide/show, edit and delete actions
def get_action_icon(type, class_id, icon):
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


# This function generates a class component with all its buttons (hide/show, edit, delete)
# The class color is used as an ID to identify a class (as all class colors are unique and cannot be modified)
def annotation_class_item(class_color, class_label):
    color = class_color
    class_color = color.replace("rgb", "rgba")
    class_color_transparent = class_color[:-1] + ",0.5)"
    class_id = str(uuid.uuid4())
    return html.Div(
        [  # This store will contain all the meta data for an individual annotation class
            dcc.Store(
                id={
                    "type": "annotation-class-store",
                    "index": class_id,
                },
                data={
                    "annotations": {},
                    "color": color,
                    "label": class_label,
                    "is_visible": True,
                    "class_id": class_id,
                },
            ),
            # These stores are solely responsible for triggereing a callback when a class is deleted or shown/hidden
            dcc.Store(id={"type": "deleted-class-store", "index": class_id}),
            dcc.Store(
                id={"type": "hide-show-class-store", "index": class_id},
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
                            dmc.ColorPicker(
                                id={
                                    "type": "edit-annotation-class-colorpicker",
                                    "index": class_id,
                                },
                                format="rgb",
                                value="rgb(255, 0, 0)",
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
            # dmc.Modal(
            #     id={"type": "edit-annotation-class-modal", "index": class_id},
            #     title="Edit a Custom Annotation Class",
            #     children=[
            #         dmc.TextInput(
            #             id={
            #                 "type": "edit-annotation-class-text-input",
            #                 "index": class_id,
            #             },
            #             placeholder="New class name...",
            #             style={"width": "70%"},
            #         ),
            #         html.Div(
            #             id={"type": "bad-edit-label", "index": class_id},
            #             style={"color": "red", "fontSize": "12px", "padding": "3px"},
            #         ),
            #         dmc.Space(h=25),
            #         html.Div(
            #             dmc.Button(
            #                 id={
            #                     "type": "relabel-annotation-class-btn",
            #                     "index": class_id,
            #                 },
            #                 children="Save",
            #             ),
            #             style={
            #                 "display": "flex",
            #                 "justify-content": "flex-end",
            #             },
            #         ),
            #     ],
            # ),
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
