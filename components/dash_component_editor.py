import re
from typing import Callable
# noinspection PyUnresolvedReferences
from inspect import signature, _empty

from dash import html, dcc, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import dash_daq as daq

import base64
#import PIL.Image
import io
#import plotly.express as px
# Procedural dash form generation



"""
{'name', 'title', 'value', 'type', 
"""


class SimpleItem(dbc.Col):     
    def __init__(self,
                 name,
                 base_id,
                 title=None,
                 param_key=None,
                 type='number',
                 debounce=True,
                 **kwargs):
        
        if param_key == None:
            param_key = name
        self.label = dbc.Label(title)
        self.input = dbc.Input(type=type,
                               debounce=debounce,
                               id={**base_id,
                                   'name': name,
                                   'param_key': param_key},
                               **kwargs)

        super(SimpleItem, self).__init__(children=[self.label, self.input])


class FloatItem(SimpleItem):
    pass


class IntItem(SimpleItem):
    def __init__(self, *args, **kwargs):
        if 'min' not in kwargs:
            kwargs['min'] = -9007199254740991  
        super(IntItem, self).__init__(*args, step=1, **kwargs)


class StrItem(SimpleItem):
    def __init__(self, *args, **kwargs):
        super(StrItem, self).__init__(*args, type='text', **kwargs)


class SliderItem(dbc.Col):
    def __init__(self,
                 name,       
                 base_id,   
                 title=None,
                 param_key=None,
                 debounce=True,
                 visible=True,
                 **kwargs):
        
        if param_key == None:
            param_key = name
        self.label = dbc.Label(title)
        self.input = dcc.Slider(id={**base_id,
                                    'name': name,
                                    'param_key': param_key,
                                    'layer': 'input'},
                                    tooltip={"placement": "bottom", "always_visible": True},
                                    **kwargs)

        style = {}
        if not visible:
            style['display'] = 'none'

        super(SliderItem, self).__init__(id={**base_id,
                                             'name': name,
                                             'param_key': param_key,
                                             'layer': 'form_group'},
                                              children=[self.label, self.input],
                                              style=style)


class DropdownItem(dbc.Col):
    def __init__(self,
                 name,       
                 base_id,  
                 title=None,
                 param_key=None,
                 debounce=True,
                 visible=True,
                 **kwargs):

        if param_key == None:
            param_key = name
        self.label = dbc.Label(title)
        self.input = dcc.Dropdown(id={**base_id,
                                    'name': name,
                                    'param_key': param_key,
                                    'layer': 'input'},
                                **kwargs)

        style = {}
        if not visible:
            style['display'] = 'none'

        super(DropdownItem, self).__init__(id={**base_id,
                                                 'name': name,
                                                 'param_key': param_key,
                                                 'layer': 'form_group'},
                                             children=[self.label, self.input],
                                             style=style)


class RadioItem(dbc.Col):
    def __init__(self,
                 name,
                 base_id,
                 title=None,
                 param_key=None,
                 visible=True,
                 **kwargs):

        if param_key == None:
            param_key = name
        self.label = dbc.Label(title)
        self.input = dbc.RadioItems(id={**base_id,
                                        'name': name,
                                        'param_key': param_key,
                                        'layer': 'input'},
                                    **kwargs)

        style = {}
        if not visible:
            style['display'] = 'none'

        super(RadioItem, self).__init__(id={**base_id,
                                               'name': name,
                                               'param_key': param_key,
                                               'layer': 'form_group'},
                                           children=[self.label, self.input],
                                           style=style)


class BoolItem(dbc.Col):
    def __init__(self,
                 name,
                 base_id,
                 title=None,
                 param_key=None,
                 visible=True,
                 **kwargs):

        if param_key == None:
            param_key = name
        self.label = dbc.Label(title)
        self.input = daq.ToggleSwitch(id={**base_id,
                                          'name': name,
                                          'param_key': param_key,
                                          'layer': 'input'},
                                      **kwargs)
        self.output_label = dbc.Label('False/True')

        style = {}
        if not visible:
            style['display'] = 'none'

        super(BoolItem, self).__init__(id={**base_id,
                                           'name': name,
                                           'param_key': param_key,
                                           'layer': 'form_group'},
                                       children=[self.label, self.input, self.output_label],
                                       style=style)


class ImgItem(dbc.Col):
    def __init__(self,
                 name,
                 src,
                 base_id,
                 title=None,
                 param_key=None,
                 width='100px',
                 visible=True,
                 **kwargs):

        if param_key == None:
            param_key = name
        
        if not (width.endswith('px') or width.endswith('%')):
            width = width + 'px'
        
        self.label = dbc.Label(title)
        
        encoded_image = base64.b64encode(open(src, 'rb').read())
        self.src = 'data:image/png;base64,{}'.format(encoded_image.decode())
        self.input_img = html.Img(id={**base_id,
                                     'name': name,
                                     'param_key': param_key,
                                     'layer': 'input'},
                                     src=self.src,
                                     style={'height':'auto', 'width':width},
                                  **kwargs)

        style = {}
        if not visible:
            style['display'] = 'none'

        super(ImgItem, self).__init__(id={**base_id,
                                           'name': name,
                                           'param_key': param_key,
                                           'layer': 'form_group'},
                                       children=[self.label, self.input_img],
                                       style=style)


class ParameterEditor(dbc.Form):

    type_map = {float: FloatItem,
                int: IntItem,
                str: StrItem,
                }

    def __init__(self, _id, parameters, **kwargs):
        self._parameters = parameters

        super(ParameterEditor, self).__init__(id=_id, children=[], className='kwarg-editor', **kwargs)
        self.children = self.build_children()

    def init_callbacks(self, app):
        app.callback(Output(self.id, 'n_submit'), 
                     Input({**self.id,
                            'name': ALL},
                            'value'), 
                     State(self.id, 'n_submit'), 
                    )
        
        for child in self.children:
            if hasattr(child,"init_callbacks"):
                child.init_callbacks(app)   
    
    
    @property
    def values(self):
        return {param['name']: param.get('value', None) for param in self._parameters} 

    @property
    def parameters(self):
        return {param['name']: param for param in self._parameters}

    def _determine_type(self, parameter_dict):
        if 'type' in parameter_dict:
            if parameter_dict['type'] in self.type_map:
                return parameter_dict['type']
            elif parameter_dict['type'].__name__ in self.type_map:
                return parameter_dict['type'].__name__
        elif type(parameter_dict['value']) in self.type_map:
            return type(parameter_dict['value'])
        raise TypeError(f'No item type could be determined for this parameter: {parameter_dict}')

    def build_children(self, values=None):
        children = []
        for parameter_dict in self._parameters:
            parameter_dict = parameter_dict.copy()
            if values and parameter_dict['name'] in values:
                parameter_dict['value'] = values[parameter_dict['name']]
            type = self._determine_type(parameter_dict)
            parameter_dict.pop('type', None)
            item = self.type_map[type](**parameter_dict, base_id=self.id) 
            children.append(item)

        return children
        

class JSONParameterEditor(ParameterEditor):
    type_map = {'float': FloatItem,
                'int': IntItem,
                'str': StrItem,
                'slider': SliderItem,
                'dropdown': DropdownItem,
                'radio': RadioItem,
                'bool': BoolItem,
                'img': ImgItem,
                #'graph': GraphItem,
                }

    def __init__(self, _id, json_blob, **kwargs):
        super(ParameterEditor, self).__init__(id=_id, children=[], className='kwarg-editor', **kwargs)
        self._json_blob = json_blob
        self.children = self.build_children()

    def build_children(self, values=None):
        children = []
        for json_record in self._json_blob:
            ...
            # build a parameter dict from self.json_blob
            ...
            type = json_record.get('type', self._determine_type(json_record))   
            json_record = json_record.copy()
            if values and json_record['name'] in values:
                json_record['value'] = values[json_record['name']]
            json_record.pop('type', None)
            item = self.type_map[type](**json_record, base_id=self.id)
            children.append(item)

        return children


class KwargsEditor(ParameterEditor):
    def __init__(self, instance_index, func: Callable, **kwargs):
        self.func = func
        self._instance_index = instance_index

        parameters = [{'name': name, 'value': param.default} for name, param in signature(func).parameters.items()
                      if param.default is not _empty]

        super(KwargsEditor, self).__init__(dict(index=instance_index, type='kwargs-editor'), parameters=parameters, **kwargs)

    def new_record(self):
        return {name: p.default for name, p in signature(self.func).parameters.items() if p.default is not _empty}
