from functools import reduce
from tokamak.models import Reactor, transformer, default_props
from tokamak.utils import pidofport
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from werkzeug.serving import WSGIRequestHandler
import json
import dash
# import dash_daq as daq
from flask_caching import Cache
import dash_html_components as html
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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP, dbc.themes.LUX]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
cache = Cache(app.server, config={
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': "/tmp"
})
app.config.suppress_callback_exceptions = True
server = app.server

DEBUG = True
timeout = 20


CACHE_CONFIG = {
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379')
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)


@cache.memoize(timeout=1)
def global_store(*args, **kwargs):
    return InterferenceGenerator(*args, **kwargs)

def optionize(*args):
    return [{"label": option, "value": option} for option in args]


@default_props({'aria-hidden': '0',
                'aria-label': lambda node: node.id,
                'valid': lambda node: isinstance(node, dcc.Dropdown)})
@cache.memoize(timeout=1)
def generate_nodes():
    nodes = [
        dcc.Dropdown(
            id="file_type",
            value="MAT",
            options=[{"label": k, "value": k} for k in ("MAT", "AWG", "PCAP")],
            label="File Type",
            renderer="labeled_form_group",
        ),
        dbc.Input(
            id="file_path",
            value="",
            type="text",
            placeholder="Enter filename to save output file",
            popover_text="hello",
            valid=False,
            renderer="labeled_form_group",
            className="validate_file_path update_file_path_popover_text",
            spellcheck="false"
        ),


        dcc.Dropdown(
            id="interference_type",
            value="TypeA",
            options=optionize("TypeA", "TypeB", "TypeC", "TypeD", "TypeE"),
            renderer="labeled_form_group",
            valid=True,
            className="update_interference_options"

        ),
        *[

        dbc.Input(
                id=f"Param{i}",
                popover_text="",
                type="number",
                valid=False,
                value=0.0,
                min=0,
                max=64,
                renderer="labeled_form_group",
                className="update_param_popover_text update_param_visibility validate_param",
                **{"aria-hidden": "1"},
            )
            for i in range(1, 14)
        ], *[
            dbc.Button(
                id="submit",
                children="submit",
                color="primary",
                block=True,
                n_clicks=0
            ),
            dcc.Markdown(
                id="clicks",
                children="",
                className="update_submit_msg"
            )
        ]]

    return nodes


# @cache.memoize(timeout=1)
class InterferenceGenerator(Reactor):


    def __init__(self, app, nodes):

        # Individual parameters are always observable, but may not always be
        # visible. Visible nodes are more or less like eigenstates, in that their
        # visibility can't be manipulated directly by the browser and it's purely a
        # function of the currently selected options.

        self._invariants = {"file_path", "file_type", "interference_type"}
        self._operators = ['file_type', 'interference_type']
        self.eigenstates = {
            "MAT": {
                "TypeA": ("Param1", "Param4"),
                "TypeB": ("Param2", "Param3"),
                "TypeC": ("Param3", "Param5", "Param8", "Param9"),
                "TypeD": ("Param2", "Param4", "Param5", "Param8", "Param9"),
                "TypeE": ("Param2", "Param6", "Param7"),
            },
            "AWG": {
                "TypeB": ("Param10", "Param11"),
                "TypeC": ("Param10", "Param12"),
                "TypeD": ("Param10", "Param12", "Param5"),
                "TypeE": ("Param10", "Param13", "Param7"),
            },
            "PCAP": {
                "TypeB": ("Param10", "Param11"),
                "TypeC": ("Param10", "Param12"),
                "TypeD": ("Param10", "Param12", "Param5"),
                "TypeE": ("Param10", "Param13", "Param7"),
            },
        }

        # for filepath validation
        self.required_ext = {"MAT": ".m", "PCAP": ".pcap", "AWG": ".wfm"}

        # cons the always-visible ids to each of the application's visible states
        for ftype, istates in self.eigenstates.items():
            for bra, ket in istates.items():
                self.eigenstates[ftype][bra] = self._invariants.union(ket)

        # Superclass will collect and bind
        #    1. nodes to matching transformer methods (if any) contained in 'className' property;
        #    2. nodes to matching renderer methods (if any) contained in 'renderer' property;
        #    3. matching transformer/renderer methods to the bundled application
        #      callback, to be executed sequentially on each clientside state update.

        super().__init__(app, nodes, DEBUG)


    def hide(self, node):
        setattr(node, "aria-hidden", "1")
        return node

    def unhide(self, node):
        setattr(node, "aria-hidden", "0")
        return node


    def update_file_path_popover_text(self, node):
        required_postfix = self.required_ext[self.nodes.file_type.value]
        has_required_postfix = self.nodes.file_path.value.endswith(required_postfix)
        is_open = not bool(has_required_postfix)
        if is_open:
            node.popover_text = f"Filepath must end with {required_postfix}"
        else:
            node.popover_text = ""
        return node

    def update_param_popover_text(self, node):
        node.popover_text = f"{node.id} must be an integer or decimal number between 0-64",
        return node

    def render_popover(self, target_id, popover_text):
        hide_popover = not bool(popover_text)
        inner_class = 'hidden' if hide_popover else 'my_tooltip col-2'
        popover = dbc.Tooltip(
            target=target_id,
            id=f'{target_id}_popover',
            trigger='focus',
            placement='right-start',
            children=popover_text,
            innerClassName=inner_class,
            autohide=False,

            hide_arrow=hide_popover,
            className='update_filepath_popover'
            #**{'aria-hidden': str(int(bool(hide_popover)))
        )
        # if node.children:
        #     node.hide_arrow = 0
        #     node.innerClassName='my_tooltip col-2'
        #
        #     setattr(node, 'aria-hidden', '0')
        # else:
        #     node.hide_arrow = 1
        #     node.children = []
        #     node.innerClassName='hidden'
        #     setattr(node, 'aria-hidden', '1')
        return popover

    @property
    def operators(self):
        return [self.nodes[operator_id] for operator_id in self._operators]


    @property
    def visible_nodes(self):
        state = self.eigenstates
        for operator in self.operators:
            state = state[operator.value]
        return state

    @property
    def interference_types(self):
        return list(self.eigenstates[self.operators[0].value].keys())

    @transformer
    def update_interference_options(self, node):
        """Equivalent to setting
                 node.options = [{'value': 'TypeA', 'label': 'TypeA'},
                                 {'value': 'TypeB', 'label': 'TypeB } ...]
           ...and so on. But it also dynamically sets this property, whose value
           is derived from the current output format."""
        node.options = optionize(*self.interference_types)
        return node

    @transformer
    def update_param_visibility(self, node):
        return self.hide(node) if node.id not in self.visible_nodes else self.unhide(node)

    @transformer
    def validate_param(self, node):
        node.valid = self.is_valid(node)
        return node

    def is_valid(self, node):
        value = node.value or 0
        return bool(value and len(str(value)))

    def ord(self, node):
        return self.nodes.index(node)

    @transformer
    def validate_file_path(self, node):
        node.valid = node.value and node.value.endswith(self.required_ext[self.operators[0].value])
        return node

    @property
    def view(self):
        return [self.render(node) for id, node in self.nodes.items()]

    def identity(self, node):
        return dbc.FormGroup([dbc.Col(node)], row=True)

    def labeled_form_group(self, node):
        row = [dbc.Col(dbc.Label(children=[node.id]), width=2),
               dbc.Col(node, width=8)]
        if hasattr(node, 'popover_text'):
            row.append(self.render_popover(node.id, node.popover_text))
        return dbc.Row(children=row, **{"aria-hidden": getattr(node, "aria-hidden")}, key=node.id)

    def prevent_invalid_submissions(self, node):
        ok = all(self.nodes[node_id].valid for node_id in self.visible_nodes)
        node.disabled = not bool(ok)
        node.active = bool(ok)
        return node
    
    def to_dict(self):
        return {node_id: self.nodes[node_id].value or 0 for node_id in sorted(self.visible_nodes, reverse=True)}
    
    def update_submit_msg(self, node):
        node.children = '\n'.join(['```',json.dumps(
            self.to_dict(),
            indent=4,
            sort_keys=True
        ), '```'])

        return node


if True:
    nodes = generate_nodes()
    app_state = InterferenceGenerator(app, nodes)


    @app_state.app.callback(*app_state.callback_dependencies)
    @cache.memoize(timeout=2)
    def callback(*args):
        return app_state.batched_callback(*args)
    # with open("/tmp/app82.dill", "wb") as f:
    #     ser = json.loads(app_state.__str__())
    #     dill.dump(ser, f)

    for node in app_state.view:
        print(node)
    try:
        app.run_server(port=8090, debug=False, dev_tools_hot_reload=False, dev_tools_props_check=False, dev_tools_prune_errors=False, dev_tools_serve_dev_bundles=True)
    except OSError as e:
        pidofport(8089, killall=True)
        app.run_server(port=8090, debug=True)
