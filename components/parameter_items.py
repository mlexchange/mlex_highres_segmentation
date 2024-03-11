import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html


class ControlItem(dmc.Grid):
    """
    Customized layout for a control item
    """

    def __init__(self, title, title_id, item, style={}):
        super(ControlItem, self).__init__(
            children=[
                dmc.Text(
                    title,
                    id=title_id,
                    size="sm",
                    style={"width": "100px", "margin": "auto", "paddingRight": "5px"},
                    align="right",
                ),
                html.Div(item, style={"width": "265px", "margin": "auto"}),
            ],
            style=style,
        )


class NumberItem(ControlItem):
    def __init__(
        self,
        name,
        base_id,
        title=None,
        param_key=None,
        visible=True,
        **kwargs,
    ):
        if param_key is None:
            param_key = name
        self.input = dmc.NumberInput(
            id={**base_id, "name": name, "param_key": param_key, "layer": "input"},
            **kwargs,
        )

        style = {"padding": "15px 0px 0px 0px"}
        if not visible:
            style["display"] = "none"

        super(NumberItem, self).__init__(
            title=title,
            title_id={
                **base_id,
                "name": name,
                "param_key": param_key,
                "layer": "label",
            },
            item=self.input,
            style=style,
        )


class StrItem(ControlItem):
    def __init__(
        self,
        name,
        base_id,
        title=None,
        param_key=None,
        visible=True,
        **kwargs,
    ):
        if param_key is None:
            param_key = name
        self.input = dmc.TextInput(
            id={**base_id, "name": name, "param_key": param_key, "layer": "input"},
            **kwargs,
        )

        style = {"padding": "15px 0px 0px 0px"}
        if not visible:
            style["display"] = "none"

        super(StrItem, self).__init__(
            title=title,
            title_id={
                **base_id,
                "name": name,
                "param_key": param_key,
                "layer": "label",
            },
            item=self.input,
            style=style,
        )


class SliderItem(ControlItem):
    def __init__(
        self,
        name,
        base_id,
        title=None,
        param_key=None,
        visible=True,
        **kwargs,
    ):
        if param_key is None:
            param_key = name
        self.input = dmc.Slider(
            id={**base_id, "name": name, "param_key": param_key, "layer": "input"},
            labelAlwaysOn=False,
            color="gray",
            size="sm",
            **kwargs,
        )

        style = {"padding": "15px 0px 15px 0px"}
        if not visible:
            style["display"] = "none"

        super(SliderItem, self).__init__(
            title=title,
            title_id={
                **base_id,
                "name": name,
                "param_key": param_key,
                "layer": "label",
            },
            item=self.input,
            style=style,
        )


class DropdownItem(ControlItem):
    def __init__(
        self,
        name,
        base_id,
        title=None,
        param_key=None,
        visible=True,
        **kwargs,
    ):
        if param_key is None:
            param_key = name
        self.input = dmc.Select(
            id={**base_id, "name": name, "param_key": param_key, "layer": "input"},
            **kwargs,
        )

        style = {"padding": "15px 0px 0px 0px"}
        if not visible:
            style["display"] = "none"

        super(DropdownItem, self).__init__(
            title=title,
            title_id={
                **base_id,
                "name": name,
                "param_key": param_key,
                "layer": "label",
            },
            item=self.input,
            style=style,
        )


class RadioItem(ControlItem):
    def __init__(
        self, name, base_id, title=None, param_key=None, visible=True, **kwargs
    ):
        if param_key is None:
            param_key = name

        options = [
            dmc.Radio(option["label"], value=option["value"])
            for option in kwargs["options"]
        ]
        kwargs.pop("options", None)
        self.input = dmc.RadioGroup(
            options,
            id={**base_id, "name": name, "param_key": param_key, "layer": "input"},
            **kwargs,
        )

        style = {"padding": "15px 0px 0px 0px"}
        if not visible:
            style["display"] = "none"

        super(RadioItem, self).__init__(
            title=title,
            title_id={
                **base_id,
                "name": name,
                "param_key": param_key,
                "layer": "label",
            },
            item=self.input,
            style=style,
        )


class BoolItem(ControlItem):
    def __init__(
        self, name, base_id, title=None, param_key=None, visible=True, **kwargs
    ):
        if param_key is None:
            param_key = name

        self.input = dmc.Switch(
            id={**base_id, "name": name, "param_key": param_key, "layer": "input"},
            label=title,
            size="sm",
            radius="lg",
            color="gray",
            **kwargs,
        )

        style = {"padding": "15px 0px 0px 0px"}
        if not visible:
            style["display"] = "none"

        super(BoolItem, self).__init__(
            title="",  # title is already in the switch
            title_id={
                **base_id,
                "name": name,
                "param_key": param_key,
                "layer": "label",
            },
            item=self.input,
            style=style,
        )


class ParameterItems(dbc.Form):
    type_map = {
        "float": NumberItem,
        "int": NumberItem,
        "str": StrItem,
        "slider": SliderItem,
        "dropdown": DropdownItem,
        "radio": RadioItem,
        "bool": BoolItem,
    }

    def __init__(self, _id, json_blob, values=None):
        super(ParameterItems, self).__init__(id=_id, children=[])
        self._json_blob = json_blob
        self.children = self.build_children(values=values)

    def _determine_type(self, parameter_dict):
        if "type" in parameter_dict:
            if parameter_dict["type"] in self.type_map:
                return parameter_dict["type"]
            elif parameter_dict["type"].__name__ in self.type_map:
                return parameter_dict["type"].__name__
        elif type(parameter_dict["value"]) in self.type_map:
            return type(parameter_dict["value"])
        raise TypeError(
            f"No item type could be determined for this parameter: {parameter_dict}"
        )

    def build_children(self, values=None):
        children = []
        for json_record in self._json_blob:
            # Build a parameter dict from self.json_blob
            type = json_record.get("type", self._determine_type(json_record))
            json_record = json_record.copy()
            if values and json_record["name"] in values:
                json_record["value"] = values[json_record["name"]]
            json_record.pop("type", None)
            if "comp_group" in json_record:
                json_record.pop("comp_group", None)
            item = self.type_map[type](**json_record, base_id=self.id)
            children.append(item)

        return children
