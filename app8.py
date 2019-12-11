from functools import reduce
from tokamak.models import Reactor, transformer, renderer, default_props
from interference.models import *
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
from interference.models import *
from interference.parameters import *
from interference.utils import *
import dash_daq as daq
from interference.models import _ns


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
DEBUG = False
timeout = 20


CACHE_CONFIG = {
    # try 'filesystem' if you don't want to setup redis
    "CACHE_TYPE": "filesystem",
    "CACHE_DIR": "/tmp/redis",
    "CACHE_REDIS_URL": os.environ.get("REDIS_URL", "redis://localhost:6379"),
}
# os.makedirs(CACHE_CONFIG['CACHE_DIR'])
# cache = Cache()
# cache.init_app(app.server, config=CACHE_CONFIG)
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



def optionize(*args):
    return [{"label": option, "value": option} for option in args]


@default_props(
    {
        "aria-hidden": "0",
        "aria-label": lambda node: node.id,
        "valid": lambda node: isinstance(node, dcc.Dropdown),
    }
)
def generate_nodes():
    return [parameter.render() for parameter in parameters]


class InterferenceGenerator(Reactor):
    def __init__(self, app, nodes, registry):
        self.registry = registry
        self.figures = []
        self.state = [0,0]
        # self.last_click = 0
        self.groupdict = registry.groupdict

        self.renderers = {k:getattr(self, v.renderer) for k,v in nodes.items()}

        # self.groupdict = nodes[0].groupdict
        # Individual parameters are always observable, but may not always be
        # visible. Visible nodes are more or less like eigenstates, in that their
        # visibility can't be manipulated directly by the browser and it's purely a
        # function of the currently selected options.
        # self._bool_switch_ids = set(
        #     [id for id, node in nodes.items() if isinstance(node, daq.BooleanSwitch)]
        # )
        self._footer_ids = ["submit", "clicks"]
        self.targets = [('submit', 'n_clicks_timestamp')]
        for node_id, node in nodes.items():
            component = node.render()
            defined_props = set(component.available_properties)
            browser_mutable_props = set(['value', 'on'])
            observable_props = defined_props.intersection(browser_mutable_props)
            self.targets.extend([(node_id, prop_name) for prop_name in observable_props])


        super().__init__(app, nodes, DEBUG)
        for node_id, node in nodes.items():
            if not callable(node.renderer):
                print(node.renderer)
                try:
                    node.renderer = getattr(self, node.renderer)
                except TypeError:
                    continue


    def hide(self, node):
        setattr(node, "aria-hidden", "1")
        return node

    def unhide(self, node):
        setattr(node, "aria-hidden", "0")
        return node

    def update_file_path_popover_text(self, node):
        required_postfix = node.required_ext[self.nodes.file_type.value]
        has_required_postfix = self.nodes.file_path.value.endswith(required_postfix)
        is_open = not bool(has_required_postfix)
        if is_open:
            node.popover_text = f"Filepath must end with {required_postfix}"
        else:
            node.popover_text = ""
        print(f"Popover text is now {node.popover_text}")
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
            hide_arrow=hide_popover,
            className="update_filepath_popover",
        )
        return popover

    @property
    def operators(self):
        return [self.nodes[operator_id] for operator_id in globals()['num_samples'].operators]
    #
    # @property
    # def visible_nodes(self):
    #     state = self.eigenstates
    #     for operator in self.operators:
    #         state = state[operator.value]
    #
    #     return state

    @property
    def interference_types(self):
        return list(self.eigenstates[self.operators[0].value].keys())

    @transformer
    def update_interference_options(self, node):
        """Equivalent to setting
                 node.options = [{'value': 'CW', 'label': 'CW'},
                                 {'value': 'hop', 'label': 'hop } ...]
           ...and so on. But it also dynamically sets this property, whose value
           is derived from the current output format."""
        node.options = optionize(*node.eigenstates[self.operators[0].value].keys())
        return node

    @transformer
    def update_param_visibility(self, node):
        return (
            self.hide(node) if node.id not in node.visible_nodes else self.unhide(node)
        )

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
        return [self.render(node) for id, node in self.nodes.items()]
        # # for
        # head = [
        #     self.render(node)
        #     for id, node in self.nodes.items()
        #     if id not in self._bool_switch_ids and id not in self._footer_ids
        # ]
        # switches = [self.labeled_button_cards()]
        # footer = [
        #     self.render(node)
        #     for id, node in self.nodes.items()
        #     if id in self._footer_ids
        # ]
        # return head + switches + footer

    def labeled_form_group(self, node):
        component = node if isinstance(node, Component) else node.render()
        row = [
            dbc.Col(dbc.Label(children=[node.id]), width=2),
            dbc.Col([component], width=8),
        ]
        if hasattr(node, "popover_text"):
            row.append(self.render_popover(node.id, node.popover_text))
        return dbc.Row(
            children=row, **{"aria-hidden": getattr(node, 'aria_hidden')}, key=node.id
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
                render_semaphore.acquire(timeout=20)
                print(f"Submit fired! Recalculating heatmap...")
                node = self.generate_interference(node)
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
            node_id: self.nodes[node_id] or 0
            for node_id in sorted(node.visible_nodes, reverse=True)}
        node.children = "\n".join(
            ["```", json.dumps(d, indent=4, sort_keys=True), "```"]
        )
        return node

    def generate_interference(self, node):
        print(f"Regenerating interference...")
        from interference.models import _ns
        # print(f"Generating interference...")
        figs = self.registry.to_matlab(_ns)
        self.figures = figs
        return node

# app.layout = html.Div(children=[], id="root")

# if __name__ == "__main__":
if True:
    ns = ParameterRegistry()
    for param in pdata:
        name = param["name"]
        obj = initialize_parameter(**dict(param, **{"ns": ns}))
        globals()[name] = obj
        ns.add(obj)
    nodes = {}
    for parameter in ns.ids:
        nodes[parameter] = globals()[parameter]
    # print(Parameter.groupdict)
    app_state = InterferenceGenerator(app, nodes, ns)
    # app.layout = app_state.view
    # app.callback_map
    # #
    # # # #
    try:
        app.run_server(port=8090,
                   debug=DEBUG,
                   dev_tools_hot_reload=False,
                   dev_tools_props_check=False,
                   dev_tools_prune_errors=True,
                   dev_tools_serve_dev_bundles=True)
    except OSError as e:
        pidofport(8089, killall=True)
        app.run_server(port=8090,
                   debug=False,
                   dev_tools_hot_reload=False,
                   dev_tools_props_check=False,
                   dev_tools_prune_errors=True,
                   dev_tools_serve_dev_bundles=True)
    # # # #
