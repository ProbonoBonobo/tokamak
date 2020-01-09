from bs4 import BeautifulSoup
import numpy as np
from functools import reduce, partial
import plotly.graph_objects as go
from interference.utils import matlab_serializer, write_to_mat, load_mat

try:
    # the try/except block is mainly to stay pep-8 compliant and avoid getting scolded about our import statements
    # being out-of-order
    from tokamak.install import apply_hotfixes

    apply_hotfixes()
except Exception as e:
    print(f"Error applying hotfixes: {e.__class__.__name__} :: {e}")
from collections import defaultdict
# from interference.parameters import pdata
from tokamak.models2 import Reactor
# from interference.models import *

from tokamak.utils import pidofport, IndexedDict
from dash.development.base_component import Component
import re
import dash_daq as daq
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from werkzeug.serving import WSGIRequestHandler
import json
import dash

# import dash_daq as daq
from flask_caching import Cache
import dash_html_components as html
import threading
import os
import datetime
import os
import random
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask_caching import Cache
from dash import no_update
from itertools import zip_longest
from numbers import Number
# from interference.models import *
# from interference.parameters import *
# from interference.utils import *
import dash_daq as daq
from interference.utils import write_to_mat
#from interference.models import _ns
import inspect

import subprocess
import os
import sys
import math
import os
import time
import subprocess
import sys

import subprocess

try:
    import matlab.engine
except Exception as e:
    print(f"{e.__class__.__name__} :: {e}")

def start_matlab_engine():
        err = None
        eng = None
        pid = None
        started = False
        try:
            import matlab.engine
        except ImportError as e:
            err = e
        if not err:
            active_pids = matlab.engine.find_matlab()
            if len(active_pids):
                pid = active_pids[-1]
                eng = matlab.engine.connect_matlab(pid)

            else:
                eng = matlab.engine.start_matlab()
                pid = os.getpid()
        started = eng is not None
        return eng, {"pid": pid, "ok": started, "err": err}
def get_matlab_bin():
    exec_path = None
    err = None
    path_to_matlab = subprocess.check_output("which matlab", shell=True, encoding='utf-8').strip()
    if os.path.isfile(path_to_matlab):
        exec_path = path_to_matlab
    elif 'MATLAB_BIN' in os.environ and os.path.isfile(os.environ['MATLAB_BIN']):
        exec_path = os.environ['MATLAB_BIN']
    else:
        err = EnvironmentError(f"Path to matlab executable could not be resolved! You may need to explicitly set this path with the 'MATLAB_BIN' environment variable.")
    print(f"Using matlab executable path of: {exec_path}")
    return err, exec_path

def install_python_matlab_engine():
        err = None
        try:
            eng, status = start_matlab_engine()
            ok = status['ok'] and eng.eval("2+2") == 4
            import matlab.engine
            return ok, None

        except ImportError:
            print(f"Matlab engine not detected. Running installer...")
        except ModuleNotFoundError:
            print(f"Matlab engine not detected. Running installer...")
        except AssertionError:
            print(f"Matlab engine not working?")
        matlab_bin = get_matlab_bin()
        get_root_cmd = f"""{matlab_bin} -batch 'fid = fopen("/tmp/out.txt", "wt"); fprintf(fid, "%s", matlabroot); fclose(fid);' && echo "$(head -n 1 /tmp/out.txt)" """
        root_dir = None
        try:
            root_dir = subprocess.check_output(get_root_cmd, shell=True, encoding="utf-8").strip()
        except Exception as e:
            err = RuntimeError(
                f"{e.__class__.__name__} :: Couldn't launch Matlab to extract the value of variable 'matlabroot'. \nError text: {e}\nShell command: {get_root_cmd}""")

        sub_dir = "extern/engines/python"
        if root_dir is None:
            for path, dirnames, filenames in os.walk("/"):
                if path.endswith(sub_dir):
                    root_dir = path[:len(sub_dir)*-1]
                    print(f"root dir is {root_dir}")
                    break

        filename = "setup.py"
        path_to_dir = os.path.join(root_dir, sub_dir)
        path_to_python_matlab_engine = os.path.join(path_to_dir, filename)
        path_to_curr_python_interpreter = sys.executable
        path = None
        eng = None
        pid = os.getpid()
        status = {}
        if not os.path.isdir(root_dir):
            err = FileNotFoundError(f"Error locating the matlab root directory! (Got: {root_dir})")
        elif not os.path.isfile(path_to_python_matlab_engine):
            err = FileNotFoundError(
                f"Error resolving the path to the matlab engine for python! Installer file {path_to_python_matlab_engine} does not exist.")
        else:
            os.chdir(path_to_dir)
            install_cmd = f"{path_to_curr_python_interpreter} setup.py install"
            proc = subprocess.run(install_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            if proc.returncode is not 0:
                err = RuntimeError(f"Error installing the python matlab bridge: {proc.stderr}")
            else:
                try:
                    eng, status = start_matlab_engine()
                    ok = status['ok'] and eng.eval("2+2") == 4
                    pid = status['pid']
                except Exception as e:
                    err = e.__class__(f"There was a problem loading the Matlab engine for python :: {e}")

        ok = err is None
        status.update({"ok": ok, "pid": pid, "err": err})

        return ok, err


def connect_matlab(session_id='foo'):
    ok, err = install_python_matlab_engine()
    try:
        eng = matlab.engine.connect_matlab(session_id)
    except matlab.engine.EngineError:
        cmd = subprocess.Popen(f'startmatlab --id="{session_id}"', shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        try:
            outs, errs = cmd.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        lockfile = f"/tmp/matlabsession_{session_id}"
        ok = False
        sleep_interval = 0.2
        max_wait = 20
        intervals = math.ceil(max_wait / sleep_interval)
        print(f"Waiting for MATLAB to generate lockfile...")
        for i in range(intervals):
            if not os.path.isfile(lockfile):
                time.sleep(0.2)
            else:
                print(f"Lockfile created.")
                with open(lockfile, 'r') as f:
                    ts = f.read()
                print(f"Session '{session_id}' initialized at {ts.strip()}")
                ok = True
                break

        if ok:
            can_connect = False
            for i in range(10):
                if session_id in matlab.engine.find_matlab():
                    print(f"Connecting to session '{session_id}'...")
                    can_connect = True
                    break
                else:
                    print(f"Waiting for session '{session_id}' to become available...")
                    time.sleep(1)
            if can_connect:
                eng = matlab.engine.connect_matlab(session_id)
            else:
                print(f"Matlab session '{session_id}' could not be loaded.")
                eng = None
        else:
            eng = None
    return eng

def convert_to_matlab_repr(param, app_state):
    self = param
    app_state = app_state
    is_bool = hasattr(param, 'is_bool') and param.is_bool
    target_prop = 'on' if is_bool else 'value'
    if hasattr(param, 'to_matlab'):
        if not callable(param.to_matlab):
            param.to_matlab = eval(param.to_matlab)
        sig = inspect.getfullargspec(param.to_matlab)
        # try:
        #     kwargs = {k:eval(k) for k in sig.kwonlyargs + sig.args}
        #     fget = lambda self=param, app_state=app_state: param.to_matlab(**kwargs)
        #
        # except Exception as e:
        #     print(e)
        #     fget = lambda self=param, app_state=app_state: getattr(self, target_prop)


    def wrapped(param):
        varname = self.matlab_alias
        if hasattr(param, 'to_matlab'):
            func = lambda app_state=app_state, param=param: param.to_matlab(app_state)
        else:
            func = lambda app_state=app_state, param=param: param.matlab_type(param.value)

        def inner(*args, **kwargs):
            value = func()
            # if hasattr(param, 'to_matlab'):
            #     value = param.to_matlab(app_state)
            if isinstance(value, bool):
                value = str(value).lower()
            elif value is None:
                value = 0
            return f"{app_state.matlab_struct_name}.{self.matlab_alias} = {value.__repr__()};"
        return inner
    return wrapped(param)

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    dbc.themes.BOOTSTRAP,
    dbc.themes.LUX,
]

app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
    serve_locally=False,
    include_assets_files=True,
)
render_semaphore = threading.RLock()
# cache = Cache(app.server, config={
#     # try 'filesystem' if you don't want to setup redis
#     'CACHE_TYPE': 'redis',
#     'CACHE_DIR': "/tmp"
# })
app.config.suppress_callback_exceptions = True
server = app.server
app.layout = html.Div(id='approot', children=[])



pdata = [
    {"id": "file_type",
     "value":"MAT",
     "constructor": dcc.Dropdown,
     "options": [{"label": k, "value": k} for k in ("MAT", "AWG", "PCAP")],
     "renderers": "labeled_form_group",
     "label": "File Type",
     "className": "",
     "group": "dbc_input_fields"},
    {"id": "file_path",
     "value": '',
     "valid": False,
     "type": "text",
     "constructor": dbc.Input,
     "className": "update_file_path_popover_text",
     "renderers": "labeled_form_group",
     "group": "dbc_input_fields",
     "spellcheck": "false",
     "tooltip": "Help"
     },
    {"id": "interference_type",
     "value": "stepchirp",
     "matlab_alias": "InterferenceType",
     "constructor": dcc.Dropdown,
      "options" : [{'label': k, 'value': k} for k in ("CW", "hop", "chirp", "stepchirp", "randFM")],
      "renderers": "labeled_form_group",
      "className" : "update_interference_options",
     },
    {"id": "num_samples",
     "value": 100000,
     "constructor": dbc.Input,
     "type": "number",
     "group": "dbc_input_fields",
     "renderers": "labeled_form_group",
     "valid": True,
     "className": "",
     "matlab_alias": "num_samples",
     "matlab_type": float},
    {"id": "isrdb",
     "constructor": dbc.Input,
     "type": "number",
     "group": "dbc_input_fields",
     "valid": True,
     "className": "",
     "value": 64,
     "matlab_alias": "ISRdB",
     "matlab_type": float},
    {
        "id": "sampling_freq",
        "value": 1e3,
        "valid": True,
        "type": "number",
        "className": "",
        "matlab_alias": "Fs",
        "matlab_type": float,
    },
    {
        "id": "n_steps",
        "value": 5.0 * 128,
        "valid": True,
        "type": "number",
        "className": "update_param_visibility",
        "matlab_alias": "Nsteps",
        "matlab_type": float,
    },
    {
        "id": "n_sweeps",
        "value": 128,
        "valid": True,
        "type": "number",
        "className": "update_param_visibility",
        "matlab_alias": "Nsweeps",
        "matlab_type": float,
    },
    {
        "id": "steps_per_chirp",
        "type": "number",
        "value": 1,
        "valid": True,
        "className": "update_param_visibility",
        "matlab_alias": "Nchirps",
        "matlab_type": float,
        "_to_matlab": lambda app_state, param: app_state.n_sweeps.value * param.value,
    },
    {
        "id": "n_hops",
        "type": "number",
        "value": 0,
        "valid": True,
        "className": "update_param_visibility",
        "matlab_alias": "Nhops",
        "matlab_type": float,
    },
    {
        "id": "bandwidth_denominator",
        "type": "number",
        "value": 16,
        "valid": True,
        "className": "update_param_visibility",
        "matlab_alias": "BandwidthDenominator",
        "matlab_type": float,

        "tooltip": """the bandwidth over which
             the hop, chirp, or random FM is allowed to span, given as the
             inverse of the proportion to the total available bandwidth.
             The minimum value of 2.0 for real signals indicates the
             interference may span from zero to Fs/2.  The minimum value of
             1.0 for complex baseband signals indicates the interference
             may span from -Fs/2 to Fs/2.  A value of 8.0 would restrict
             the span of the interference to -Fs/16 to Fs/16 for complex,
             or 3*Fs/16 to 5*Fs/16 for real.""",
    },
    {
        "id": "cw_frequency_offset",
        "type": "number",
        "value": 0,
        "matlab_alias": "CWfreqOffset",
        "valid": True,
        "className": "update_param_visibility",
        "matlab_type": float,
        "tooltip": """the offset of the frequency of the CW interferer from Fs/4 in the
             case of real samples, or from zero in the case of complex
             samples.""",
    },
    {
        "id": "randfm_moving_average",
        "value": 0,
        "type": "number",
        "matlab_alias": "RandFMMovingAverage",
        "matlab_type": int,
        "valid": True,
        "className": "update_param_visibility",
        "tooltip": """a volatility selector for the frequency of the random FM
             interference.  Smaller values make the interferer more volatile
             and larger values make it move around the band more sluggishly.""",
    },
    {
        "id": "randfm_centering",
        "value": 8,
        "type": "number",
        "matlab_alias": "RandomFMCentering",
        "matlab_type": float,
        "valid": True,
        "className": "update_param_visibility",
        "tooltip": """centering selector for the frequency of the
             random FM interference, controlling its propensity to move
             closer to the center of the band when out near the edge.
             Smaller values allow it to spend more time out near the edges,
             while larger values cause it to be more strongly mean-
             reverting.  Too-small values could cause it to rail at one
             edge of the band indefinitely, while too-large values could
             cause it to look almost like an on-carrier CW.""",
    },
    {
        "id": "continuous_phase",
        "value": 1,
        "type": "number",
        "is_bool": True,
        "matlab_alias": "ContinuousPhase",
        "matlab_type": bool,
        "constructor": daq.BooleanSwitch,
        "className": "print_boolswitch update_param_visibility",
        "tooltip": """ if true, the phase of the interferer is preserved
             from one sample to the next across hops, steps, or chirp resets
             to the opposite side of the band; if false, when the interferer
             hops, steps, or resets to the opposite side of the band, the
             first sample of the new frequency is given a random phase
             unrelated to the last sample of the old frequency, or the
             StartingPhase value, depending on SpecifyStartingPhase.""",

    },
    {
        "id": "random_start_freq",
        "is_bool": True,
        "value": 1,
        "className": "print_boolswitch update_param_visibility",
        "constructor": daq.BooleanSwitch,
        "matlab_type": bool,
        "matlab_alias": "RandomStartFreq",
        "tooltip": """if true, the first sweep of the chirp will begin
             at a random frequency within the band, sweep to the high edge
             of the band, and then reset to the low edge; if false, the
             first sweep of the chirp will always begin at the low edge of
             the band.""",
    },
    {
        "id": "use_bandpass_data",
        "is_bool": True,
        "value": 0,
        "on": False,
        "constructor": daq.BooleanSwitch,
        "matlab_type": bool,
        "className": "print_boolswitch update_param_visibility",
        "matlab_alias": "UseBandpassData",
    },
    { "id": "submit",
      "constructor": dbc.Button,
      "value": 0,
      "children": "submit",
      "color": "primary",
      "renderer": "button_renderer",
      "block": True,
      "className": "",
      "type": "button",
      "n_clicks" : 0,
      "on_click": "generate_interference",
      "n_clicks_timestamp": 0,
      "group": "footer"},
    # {"id": "graph_container",
    #  "constructor": html.Div,
    #  "children": [],
    #  "value": None,
    #  "className":

    {"id": "graph_container",
     "constructor": dbc.Container,
     "renderers": "show_figures",
     "children" : []},
    {"id": "clicks",
     "constructor": dcc.Markdown,
     "children": "",
     "value": "",

     "className": "",
     "group": "footer"}
]
_ids = set([node['id'] for node in pdata])

def optionize(*args):
    return [{"label": option, "value": option} for option in args]

class App(Reactor):
    matlab_struct_name = "InterferenceConfig"
    python_only_parameters = {"submit", "clicks", "file_path"}
    _operators = ["file_type", "interference_type"]
    required_ext = {"MAT": ".m", "PCAP": ".pcap", "AWG": ".wfm"}
    eigenstates = {
        "MAT": {
            "CW": ("sampling_freq", "cw_freq_offset"),
            "hop": ("n_hops", "bandwidth_denominator"),
            "chirp": (
                "bandwidth_denominator",
                "n_sweeps",
                "n_chirps",
                "continuous_phase",
                "random_start_freq",
            ),
            "stepchirp": (
                "bandwidth_denominator",
                "n_sweeps",
                "steps_per_chirp",
                "continuous_phase",
                "random_start_freq",
            ),
            "randFM": (
                "bandwidth_denominator",
                "randfm_moving_average",
                "randfm_centering",
            ),
        },
        "AWG": {
            "hop": ("Bandwidth", "DwellTime"),
            "chirp": ("Bandwidth", "ChirpRate"),
            "stepchirp": ("Bandwidth", "ChirpRate", "n_sweeps"),
            "randFM": ("Bandwidth", "MovingAvgLength", "RandomFMCentering"),
        },
        "PCAP": {
            "hop": ("Bandwidth", "DwellTime"),
            "chirp": ("Bandwidth", "ChirpRate"),
            "stepchirp": ("Bandwidth", "ChirpRate", "n_sweeps"),
            "randFM": ("Bandwidth", "MovingAvgLength", "RandomFMCentering"),
        },
    }
    always_visible_ids = {'isrdb', 'num_samples', 'file_path', 'file_type', 'interference_type', 'use_bandpass_data', 'graph_container'}
    def __init__(self, app, parameter_definitions):
        self.figures = []
        self.engine = connect_matlab()
        self.nodes = self.initialize_parameters(parameter_definitions)
        super().__init__(app, self.nodes)

    def say_hello(self, node):
        print(f"Node {node.id} (value: {node.value}) says hello!")
        return node

    def print_bar(self, node):
        print(f"Node {node.id} is: {'ON' if node.on else 'OFF'}")
        node.value = node.on
        return node


    def write_to_matlab(self):
        def convert_to_matlab_repr(param):
            varname = param.matlab_alias
            value = param.matlab_type(param.value)
            if hasattr(param, 'to_matlab'):
                try:
                    value = param.to_matlab(app_state)
                except Exception as e:
                    trace = sys.gettrace()
                    print(f"Got {e.__class__.__name__} while writing parameter {varname} to matlab representation :: {e}")
                    print(f"Value of {varname}: {param.value}")
                    print(trace)
                    breakpoint()

            if isinstance(value, bool):
                return str(value).lower()
            elif value is None:
                return 0
            else:
                return value

        lines = ["Here is your matlab program:"]
        for id, node in self.nodes.items():
            matlabized = convert_to_matlab_repr(node.value).__repr__()
            lines.append(f"InterferenceConfig.{node.id} = {matlabized};")
        program = '\n'.join(lines)
        print(program,end="\n\n\n")
    def update_file_path_popover_text(self, node):
        required_postfix = {"MAT": ".m", "AWG": ".wfm", "PCAP": ".pcap"}[self.nodes['file_type'].value]
        has_required_postfix = self.nodes['file_path'].value.endswith(required_postfix)
        is_open = not bool(has_required_postfix)
        if is_open:
            node.tooltip = f"Filepath must end with {required_postfix}"
            node.valid = False
        else:
            node.tooltip = ""
            node.valid = True

        return node

    def identity(self, node):
        return node.render() if hasattr(node, 'render') else node
    # @cache.memoize(timeout=10)
    def render_popover(self, target_id, popover_text):
        hide_popover = not bool(popover_text)
        inner_class = "hidden" if hide_popover else "my_tooltip col-2"
        popover = dbc.Tooltip(
            target=target_id,
            id=f"{target_id}_popover",
            trigger="focus",
            placement="right-start",
            children=popover_text,
            innerClassName=inner_class,
            autohide=False,
            # hide_arrow=hide_popover,
            className="update_filepath_popover",
        )
        return popover

    @property
    def operators(self):
        return [self.nodes[operator_id] for operator_id in self._operators]

    #
    @property
    def visible_nodes(self):
        state = self.eigenstates
        for operator in self.operators:
            state = state[operator.value]
        return set(state).union(self.python_only_parameters, self.always_visible_ids)
        return state


    @property
    def interference_types(self):
        return list(self.eigenstates[self.operators[0].value].keys())

    def update_interference_options(self, node):
        """Equivalent to setting
                 node.options = [{'value': 'CW', 'label': 'CW'},
                                 {'value': 'hop', 'label': 'hop } ...]
           ...and so on. But it also dynamically sets this property, whose value
           is derived from the current output format."""
        node.options = optionize(*self.eigenstates[self.operators[0].value].keys())
        return node

    def update_param_visibility(self, node):
        print(f"updating visibility of {node.id}")
        node.__setattr__('aria-hidden', str(int(not bool(node.id in self.visible_nodes))))
        return node

    # @transformer
    def validate_param(self, node):
        node.valid = self.is_valid(node)
        return node

    def is_valid(self, node):
        value = node.value or 0
        return bool(value and len(str(value)))

    def ord(self, node):
        return self.nodes.index(node)

    # @transformer
    def validate_file_path(self, node):
        node.valid = node.value and node.value.endswith(
            node.required_ext[self.operators[0].value]
        )
        return node

    @property
    def view(self):
        return [reduce(lambda node, renderer: renderer(node), [node, *self.renderers[id]]) for id, node in self.nodes.items()]


    def labeled_form_group(self, node):
        component = node if isinstance(node, Component) else node.render()
        row = [
            dbc.Col(dbc.Label(children=[node.id]), width=2),
            dbc.Col([component], width=8),
        ]
        if hasattr(node, "tooltip"):
            row.append(self.render_popover(node.id, node.tooltip))
        return dbc.Row(
            children=row, **{"aria-hidden": getattr(self.update_param_visibility(node), 'aria-hidden')}, key=node.id
        )

    # def labeled_button_cards(self):
    #     rows = dbc.Container(
    #         children=[], fluid=False, className="bool-switch-container"
    #     )
    #     for nodelist in grouper([self.nodes[id] for id in self._bool_switch_ids], 5):
    #         nodelist = [
    #             node for node in nodelist if isinstance(node, daq.BooleanSwitch)
    #         ]
    #         nodecount = len(nodelist)
    #         width = int(12 / nodecount if nodecount else 12)
    #         row = dbc.CardGroup(
    #             [
    #                 dbc.Card(
    #                     dbc.CardBody(
    #                         [html.H4(node.label, className="param-label"), node]
    #                     ),
    #                     enabled="1" if node.on else "0",
    #                     className="param-card",
    #                 )
    #                 for node in nodelist
    #             ],
    #             className="bool-switch-cardgroup",
    #         )
    #
    #         for node in nodelist:
    #             if hasattr(node, "popover_text"):
    #                 row.children.append(self.render_popover(node.id, node.popover_text))
    #         rows.children.append(row)
    #     return rows

    def print_boolswitch(self, node):
        print(f"Node {node.id} is {'ON' if node.on else 'OFF'}")

    def labeled_buttons(self):
        rows = dbc.Container(
            children=[], fluid=False, className="bool-switch-container"
        )
        for nodelist in grouper([self.nodes[id] for id in self._bool_switch_ids], 3):
            nodecount = len(
                [node for node in nodelist if isinstance(node, daq.BooleanSwitch)]
            )
            width = int(12 / nodecount if nodecount else 12)
            row = dbc.Row(
                [dbc.Col(node, width=width) for node in nodelist],
                className="bool-switch-row",
            )
            for node in nodelist:
                if hasattr(node, "popover_text"):
                    row.append(self.render_popover(node.id, node.popover_text))
            rows.children.append(row)
        return rows

    def button_renderer(self, node):
        # component = node if isinstance(node, Component) else node.render()
        self.state.append('\n'.join(write_to_mat(_ns, _ns.num_samples.visible_nodes)))
        print(f"Rendering button (clicked at {ns.submit.n_clicks_timestamp} )")
        print(red(self.state[-2]))
        print(green(self.state[-1]))
        if self.state[-2] == self.state[-1]:
            print(f"State is identical. Renderer blocked.")
        else:
            print(f"States are different. Rendering...")
            if render_semaphore._is_owned():
                print(f"State has changed, but renderer is currently blocked.")
            else:
                render_semaphore.acquire(timeout=30)
                print(f"Submit fired! Recalculating heatmap...")
                figs = self.generate_interference()
                self.last_click += 1
                try:
                    render_semaphore.release()
                except RuntimeError:
                    pass
                # self.last_click = node.n_clicks
        return dbc.Container(children=[dbc.Row([dbc.Col(
            node.constructor(children=node.children,
                             color=node.color,
                             block=node.block,
                             id=node.id,
                             className=node.className))]),
            *[dbc.Row([dcc.Graph(figure=fig)]) for i, fig in enumerate(reversed(self.figures))]])
        # return dbc.Container([dbc.Row(dbc.Col(dbc.Button("Submit", id='submit', block=True, color='dark'))),
        #     dbc.Row(dbc.Col(children=[html.P("hello i'm a child"), *self.figures]))])

    def to_dict(self):
        return {
            node_id: self.nodes[node_id] or 0
            for node_id in sorted(self.visible_nodes, reverse=True)
        }

    def update_submit_msg(self, node):
        d = {
            node_id: self.nodes[node_id].value or 0
            for node_id in sorted(self.visible_nodes, reverse=True)}
        node.children = self.transpile_to_mat()
        return node

    # def generate_interference(self, node):
    #     print(f"Regenerating interference...")
    #     from interference.models import _ns
    #     # print(f"Generating interference...")
    #     figs = self.registry.to_matlab(_ns)
    #     self.figures = figs
    #     return node

    def transpile_to_mat(self):
        return '\n'.join([f"NumSamples = {self.num_samples.value};", *[param.to_matlab()
                                                                       for id, param
                                                                       in self.nodes.items()
                                                                       if id in self.visible_nodes]])


    def initialize_parameters(self, pdata):
        params = {}
        for d in pdata:
            print(d)
            data = defaultdict(lambda: None, d)
            constructor = data['constructor'] or dbc.Input
            data['aria-hidden'] = "0"
            print(constructor)



            param = constructor(**data)
            try:
                param.tooltip = re.sub(r'\s+', r' ', param.tooltip)
            except AttributeError:
                pass
            if not hasattr(param, 'renderers'):
                param.renderers = 'labeled_form_group'
            if param.renderers == 'labeled_form_group':
                if 'update_param_visibility' not in param.className:
                    param.className += " update_param_visibility"
            if not hasattr(param, 'is_bool'):
                param.is_bool = param.constructor == daq.BooleanSwitch
            if not hasattr(param, 'matlab_alias'):
                param.matlab_alias = param.id
            if not hasattr(param, 'value'):
                if param.constructor == daq.BooleanSwitch:
                    param.value = param.on
                else:
                    param.value = ''
            if not hasattr(param, 'matlab_type'):
                param.matlab_type = type(param.value) if hasattr(param, 'value') else float
                if param.matlab_type is float and param.value is None:
                    param.value = 0
            # if hasattr(param, 'to_matlab'):
            #     f = eval(param.to_matlab)
            #     param.to_matlab =
            # print(param)
            print(f"Generating to_matlab method for {param.id}...")
            # f = copy(param.to_matlab)
            def convert(func):
                def inner(*args, **kwargs):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        return str(e) + f" (Value was: {locals()}"
                return inner
            if not hasattr(param, '_to_matlab'):

                    param._to_matlab = convert(partial(lambda app_state, param, is_bool=param.is_bool: param.matlab_type(param.value).__repr__() if not is_bool else str(param.on).lower(), app_state=self, param=param))
            else:
                    param._to_matlab = convert(partial(param._to_matlab, app_state=self, param=param))
            if param.id in self.python_only_parameters:
                param.to_matlab = lambda: ""
            else:

                param.to_matlab = partial(lambda app_state, param: f"InterferenceConfig.{param.matlab_alias} = {param._to_matlab()};",
                                          app_state=self, param=param)

            params[param.id] = param
        return params

    def __getattr__(self, item):
        if item in _ids:
            return self.nodes[item]
        else:
            return object.__getattribute__(self, item)
    def generate_interference(self):
        import subprocess
        path_to_matlab = '/home/kz/.local/MATLAB/bin/matlab'
        print(f"To matlab called")
        cmd = {}

        serialized = self.transpile_to_mat()
        lines = []
        filepath= f'/home/kz/share/my_results.json'
        # lines.append("diary /home/kz/share/log.txt;")
        # lines.append("diary on;")
        lines.append("cd /home/kz/share;")
        # lines.append("addpath('/home/kz/share/jsonlab');")
        lines.append(serialized)
        lines.append(f"Input = GenerateInterference(NumSamples, InterferenceConfig);")
        lines.append(f"input_arr = abs(Input);")
        lines.append(f"fig0 = specgram(Input);")
        lines.append(f"input_fig = abs(fig0);")
        lines.append(f"Output = Software_results(Input);")
        lines.append(f"output_arr = abs(Output);")
        lines.append(f"fig1 = specgram(Output);")
        lines.append(f"output_fig = abs(fig1);")
        # lines.append(f"ns = struct('input_fig', input_fig, 'output_fig', output_fig);")
        # lines.append(f"ns = jsonencode(ns);")

        # lines.append(f"savejson('Results', ns, '{filepath}');")
        # lines.append("diary off;")


        for line in lines:
            try:
                self.engine.eval(line, nargout=0)
            except Exception as e:
                print(f"{e.__class__.__name__} while executing line '{line}': {e}")
                continue

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
        # figs = load_mat(filepath, keys=['input_fig', 'output_fig'])
        try:
            arr0 = self.engine.eval("input_fig")
            arr1 = self.engine.eval("output_fig")
        except Exception as e:
            print(sys.gettrace())
            print(f"Couldn't get ns.input_fig: {e}")

        z0 = np.array(arr0, dtype=np.float64).tolist()
        z1 = np.array(arr1, dtype=np.float64).tolist()
        #z0 = [float(x) for self.engine.eval('input_fig'))
        #z1 = list(self.engine.eval('output_fig'))
        fig0 = go.Heatmap(z=z0)
        fig1 = go.Heatmap(z=z1)


        self.figures = [fig0, fig1]
        return self.figures
        # script = '\n'.join(lines)
        # with open("/home/kz/share/testing2.m", 'w') as f:
        #     f.write(script)
        # print(f"Text of testing2.m:")
        # print(script)
        # output = subprocess.check_output(f"""cd /home/kz/share && {path_to_matlab} -nosplash -nodesktop -r 'run("/home/kz/share/testing2.m"); quit;'""", shell=True)
        # parsed_html = BeautifulSoup(output)
        # text_only = parsed_html.text
        # print(f"Process finished. Output is:\n\n {text_only}")
        # self.figures = load_mat(filepath, ['input_fig', 'output_fig'])



    def show_figures(self, node):
        node.children = [dbc.Row([dbc.Col(dcc.Graph(figure={"data": [fig]}))]) for i, fig in enumerate(reversed(self.figures))]
        return node






import dash_core_components as dcc
import dash_bootstrap_components as dbc



if __name__ == '__main__':

    # nodes = {node.id:node for node in [dbc.Input(id='foo', type='text', value='', className='say_hello', debounce=True),
    #                                    daq.BooleanSwitch(id='bar', on=True, className='print_bar'),
    #                                    html.Button(id='submit', block=True, on_click='write_to_matlab')]}
    app_state = App(app, pdata)
    app_state.app.run_server(port=8888)

    # foo = dbc.Input(id='foo', hidden="lambda self: str(self.value)", value='hello')


    # app_state.app.run_server(port=8003, debug=True, dev_tools_hot_reload=True)
    # app.run_server(port=8000)
