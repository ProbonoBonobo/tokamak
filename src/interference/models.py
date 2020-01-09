import time
from interference.utils import matlab_serializer, write_to_mat, load_mat
from interference.parameters import pdata
from collections import Hashable
import json
from tokamak.utils import logger
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import random
from functools import partial
from collections import defaultdict, deque, OrderedDict, Counter
import inspect
from dash import no_update
import dash_html_components as html
import datetime
from gemeinsprache.utils import *
from tokamak.utils import pp, pidofport
import dash
from multiprocessing import RLock
from dash.development.base_component import Component
from typing import Tuple
from tokamak.utils import to_serializable
from flask_caching import Cache
import functools

from tokamak.utils import IndexedDict
import dash_daq as daq
from bs4 import BeautifulSoup
import weakref
from interference.utils import matlab_serializer
from munch import Munch
_members = []
_id2index = {}
from tokamak.utils import to_serializable
_ns = Munch()

path_to_matlab = "/home/kz/.local/bin/matlab"

class ParameterRegistry(object):
    num_samples = None
    data = IndexedDict()
    ids = []


    @property
    def count(self):
        return len(_members)

    def add(self, parameter):
        #self.data[parameter.name] = weakref.ref(parameter)
        # proxy = weakref.ref(parameter)
        # proxy.__hash__()
        _ns[parameter.name] = parameter
        if parameter.name not in self.ids:
            self.ids.append(parameter.name)
        print(f"Adding {parameter.name} to cache")
        #print(self.data[parameter.name])
        #print(regular_dict)
        # weak references shall hash to the same value as the canonical object
        # as long as the hash is computed before the canonical object has been
        # garbage collected. that seems like a good thing, so let's go ahead
        # and compute it at instantiation time

    def to_matlab(self, eng=None):
        print(f"To matlab called")
        cmd = {}
        visible_params = Parameter().visible_nodes
        transpiled = self.transpile_to_mat()
        serialized = json.dumps(cmd, default=matlab_serializer)
        lines = []
        filepath= f'/home/kz/share/my_results.json'
        lines.append("diary /home/kz/share/log.txt;")
        lines.append("diary on;")
        lines.append("cd /home/kz/share;")
        lines.append("addpath('/home/kz/share/jsonlab');")
        lines.extend(transpiled)
        lines.append(f"Input = GenerateInterference(NumSamples, InterferenceConfig);")
        lines.append(f"input_arr = abs(Input);")
        lines.append(f"fig0 = specgram(Input);")
        lines.append(f"input_fig = abs(fig0);")
        lines.append(f"Output = Software_results(Input);")
        lines.append(f"output_arr = abs(Output);")
        lines.append(f"fig1 = specgram(Output);")
        lines.append(f"output_fig = abs(fig1);")
        lines.append(f"ns = struct('input_arr', input_arr, 'input_fig', input_fig, 'output_arr', output_arr, 'output_fig', output_fig);")
        # lines.append(f"ns = jsonencode(ns);")

        lines.append(f"savejson('Results', ns, '{filepath}');")
        lines.append("diary off;")
        for line in lines:
            eng.eval(line, nargout=0)

        # script = '\n'.join(lines)
        # with open("/home/kz/share/testing2.m", 'w') as f:
        #     f.write(script)
        # print(f"Text of testing2.m:")
        # print(script)
        #
        # output = subprocess.check_output(f"""cd /home/kz/share/ && {path_to_matlab} -nosplash -nodesktop -r 'run("/home/kz/share/testing2.m"); quit;'""", shell=True)
        # parsed_html = BeautifulSoup(output)
        # text_only = parsed_html.text
        # print(f"Process finished. Output is:\n\n {text_only}")
        figs = load_mat(filepath, ['input_fig', 'output_fig'])
        fig0 = eng.eval("input_fig")
        fig1 = eng.eval("output_fig")
        return [fig0, fig1]




    def __setattr__(self, item, value):
        try:
            super().__setattr__(item, value)
        except Exception as e:
            # print(e.__class__.__name__ + " " + str(e))
            object().__setattr__(item, value)
        # print(self.__getattr__(item))
        # self.group[self.__getattr__(item).render_group].add(self.__getattr__(item))

        # return obj

    def __getattr__(self, item):
        if item == 'groupdict':
            obj = Parameter.groupdict
        elif item == 'items':
            obj = lambda _ns=_ns: _ns.toDict().items()
        else:
            try:
                obj = super().__getattribute__(item)
            except Exception as e:
                if hasattr(self, 'ids') and item in self.ids:
                    obj = _ns[item]
                    if obj is not None:
                        return obj
                else:
                # print(e.__class__.__name__ + " " + str(e))
                    obj = object().__getattribute__(item)

        # if isinstance(obj, Parameter):
        #     return obj.value
        return obj
# ns = ParameterRegistry()

import inspect


class Parameter:
    members = _members
    id2index = _id2index
    groupdict = defaultdict(set)
    invariants = {
            "isrdb",
            "use_bandpass_data",
            "file_path",
            "file_type",
            "interference_type",
            "submit",
            "clicks"}

    def __init__(self, *args, **kwargs):
        # for prop in self.invariants:
            for filetype, data in self.eigenstates.items():
                for interference_type, visible_ids in data.items():
                    data[interference_type] = set(list(visible_ids) + list(self.invariants))

    @property
    def visible_nodes(self):
        state = self.eigenstates
        for operator in self.operators:
            try:
                state = state[_ns[operator].value]
            except Exception as e:
                print(e)
                state = []
        return state

    @property
    def aria_hidden(self):
        return str(int(not bool(self.id in self.visible_nodes)))

    @staticmethod
    def transform_wildcard_propnames(rendered_props):
        return {re.sub(r"aria_", "aria-", k): v for k,v in rendered_props.items()}






    # def __getattr__(self, item):
    #     print(f"Superget: {locals()}")
    #     if item in _id2index:
    #         return _members[_id2index[item]]
    #     raise AttributeError
    # def __setattr__(self, attr, value):
    #     print(f"superset: {locals()}")
    #     try:
    #         self.__dict__[attr] = initialize_parameter(attr, value)
    #
    #     except Exception as e:
    #         print(e)
    #         self.__dict__[attr] = value




def hashable(x):
    ok = not callable(x) and isinstance(x, Hashable) and not isinstance(x, Component)
    if ok:
        try:
            json.dumps(x)
            return True
        except:
            return False
    return False

def initialize_parameter(
    name,
    initial_value,
    constructor=dbc.Input,
    label=None,
    ord=None,
    is_bool=False,
    matlab_alias=None,
    matlab_type=None,
    to_matlab=None,
    awg_alias=None,
    awg_type=None,
    pcap_alias=None,
    pcap_type=None,
    min=None,
    max=None,
    options=None,
    tooltip="",
    className="",
    group="",
    **kwargs,
):

    base_class = type(initial_value)

    def constantly(var):
        def only_var():
            return var.value

        return only_var()

    this = globals()[name] if name in globals() else None

    class PolymorphicallyTypedParameter(Parameter):
        serializable_fields = set()
        def __init__(self, value):
            self.name = name
            self.id = self.name
            self.value = value
            self.on = bool(value)
            self.base_class = base_class
            self.label = label or self.id
            self.is_boolean = bool(is_bool)
            self.constructor = constructor or dbc.Input if not is_bool else daq.BooleanSwitch
            self.className = className if className is not None else (
                "update_param_visibility validate_param"
                if not self.is_boolean
                else "boolswitch"
            )
            self.renderer = "labeled_form_group" if not self.is_boolean else "identity"
            self.initial_value = initial_value
            self.matlab_alias = matlab_alias or name
            self.matlab_type = matlab_type or base_class

            self.awg_alias = awg_alias or name
            self.awg_type = awg_type or base_class
            self.pcap_alias = pcap_alias or name
            self.pcap_type = pcap_type or base_class


            self.popover_text = re.sub(r'\s+', ' ', tooltip) or f"This is the tooltip for {self.name}."
            self.min = min or 0
            self.max = max or 256
            self.render_group = group
            if not self.render_group:
                if self.is_boolean:
                    self.render_group = "switchboard"
                elif constructor == dbc.Input:
                    self.render_group = "dbc_input_fields"
                else: self.render_group = 'footer'
            self.type = "text" if isinstance(self.value, str) else "number"
            self.options = options or []
            self.n_clicks = 0
            self.n_clicks_timestamp = 0
            # setattr(ParameterRegistry, self.name, self)
            # ParameterRegistry.data[self.name] = self
            # # setattr(self, "aria-hidden", "0")
            # globals()[self.name] = self
            super().__init__()
            print(f"Adding {self.name} to render group {self.render_group}")

            # super().groupdict[self.render_group].add(self.id)
            # self.rendered = self.render()
            for k,v in self.__dict__.items():
                if isinstance(v, Hashable):
                    self.serializable_fields.add(k)
                elif k == 'options':
                    self.serializable_fields.add(k)
            self.__dict__.update(kwargs)


        # @property
        # def on(self):
        #     self.value = bool(self.value)
        #     return bool(self.value) if hasattr(self, 'value') else False
        #
        # @on.setter
        # def toggle_switch(self, value):
        #     self.value = bool(self.value)
        #     return self.value

        def props(self):
            return {k:getattr(self, k) for k in self.serializable_fields}

        def render(self):
            args = self.transform_wildcard_propnames(self.props())
            rendered = self.constructor(**args)
            if self.name == 'submit':
                try:
                    rendered = self.renderer(self.constructor(id=self.id, children='submit', className=self.className, block=True, color='dark'))
                except:
                    pass
            # if callable(self.renderer):
            #     rendered = self.renderer(rendered)
            return rendered
            # args = {k:v for k,v in self.__dict__.items() if not k.startswith("_") and not callable(v)}
            # print(args)
            # self.rendered = self.constructor(**args)
            # return self.rendered

        def __set__(self, obj, value):
            # super().__init__(value)
            self.value = value

        def __add__(self, other):
            if isinstance(other, Parameter):
                other = other.value
            return self.value + other

        def __sub__(self, other):
            if isinstance(other, Parameter):
                other = other.value
            return self.value - other

        def __mul__(self, other):
            if isinstance(other, Parameter):
                other = other.value
            return self.value * other

        def __repr__(self):
            return str(self.value)

        #
        # def __str__(self):
        #     return str(self.value)

        # globals()[self.name] = obj.__getattribute__(self.name)
        def __get__(self, obj, objtype, val_only=True):
            print(f"Get called: {locals()}")
            # print(inspect.stack()[1])
            # if self.name in globals() and globals()[self.name] != self:
            #     self.value = globals()[self.name]
            #     globals()[self.name] = self

            return self
            # if hasattr(obj, self.name):
            #     return obj.__getattr__(self.name)
            # return s

        def to_plotly_json(self):
            return self.render().to_plotly_json()

        # def __getattr__(self, attr):
        #     try:
        #         if hasattr(self.__dict__['rendered'](), attr):
        #             return getattr(self.__dict__['render'](), attr)
        #         return super().__getattribute__(attr)
        #     except KeyError:
        #         return super().__getattribute__(attr)
    for prop_name, prop_value in inspect.getmembers(PolymorphicallyTypedParameter):
        serializable = hashable(prop_value)
        print(f"Prop: {prop_name} (value: {prop_value}, {type(prop_value).__name__} {'is' if serializable else 'is NOT'} serializable")
        if serializable:
            PolymorphicallyTypedParameter.serializable_fields.add(prop_name)

    # breakpoint()
    instantiated = PolymorphicallyTypedParameter(initial_value)
    ns.add(instantiated)
    # globals()[instantiated.name] = weakref.ref(instantiated)
    # prop = property(instantiated, lambda self, obj: Parameter.members[instantiated.ord], lambda self, obj, value: PolymorphicallyTypedParameter(value))
    #setattr(ParameterRegistry, name, instantiated)
    #globals()[name] = ParameterRegistry.__getattribute__(parameter, name)
    return instantiated

# ns.to_matlab(_ns)
