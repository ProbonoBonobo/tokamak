from gemeinsprache.utils import *
import datetime
from typing import Mapping
from collections import defaultdict, deque
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash
import dash_html_components as html
from dash.development.base_component import Component
import json
import dash
from dash import callback_context
from dash import no_update
try:
    # the try/except block is mainly to stay pep-8 compliant and avoid getting scolded about our import statements
    # being out-of-order
    from tokamak.install import apply_hotfixes

    apply_hotfixes()
except Exception as e:
    print(f"Error applying hotfixes: {e.__class__.__name__} :: {e}")

required_props = {'value': ''}

callback_triggers = {
                     "n_blur_timestamp": -1,
                 "on": False,
                 # "n_clicks": -1,
                 # "n_clicks_timestamp": -1,
                 "state": {},
                 "n_intervals": -1}
mutable_props = {"value": ""}

python_only_props = {"renderers",
                     "async_transformers",
                     "targets",
                     "sockets",
                     "on_click"}

default_navbar =         navbar = dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("Link", href="#")),
                dbc.DropdownMenu(
                    nav=True,
                    in_navbar=True,
                    label="Menu",
                    children=[
                        dbc.DropdownMenuItem("Entry 1"),
                        dbc.DropdownMenuItem("Entry 2"),
                        dbc.DropdownMenuItem(divider=True),
                        dbc.DropdownMenuItem("Entry 3"),
                    ],
                ),
            ],
            brand="Interference Generator",
            brand_href="#",
            sticky="top",
            color="dark",
            dark=True,
            style={"color": "#EEEEEE"},
        )


class Reactor:

    mutable_props = mutable_props
    required_props = required_props
    trigger_props = callback_triggers
    _external_stylesheets = [
        "https://codepen.io/chriddyp/pen/bWLwgP.css",
        dbc.themes.BOOTSTRAP,
        dbc.themes.LUX,
    ]

    def __init__(self, app=None, nodes={}, external_stylesheets=None, navbar=default_navbar):
        self.nodes = self.index_nodes(nodes)
        self.ids = tuple(list(self.nodes.keys()))
        self._sockets = {id: html.Div(id=f"_{id}__socket", children=html.Div(id=f"{id}__socket", children=node)) for id, node in self.nodes.items()}
        self.external_stylesheets = external_stylesheets or self._external_stylesheets
        self.navbar = navbar
        self.app = app
        self.targets = self.acquire_targets()
        self.async_channels = self.acquire_async_targets()
        self.intervals = self.initialize_intervals()
        self.async_transformers = self.resolve_async_transformers()
        self.transformers = self.resolve_transformers()
        self.renderers = self.resolve_renderers()
        self.click_handlers = self.resolve_click_handlers()
        self.callback = self.generate_callback()
        self.eventloop = self.generate_async_callbacks()

        self.app.layout = self.set_initial_layout()
    def index_nodes(self, nodes):
        if isinstance(nodes, Mapping) and all(isinstance(v, Component) and k == v.id for k,v in nodes.items()):
            return nodes
        elif isinstance(nodes, list) and all(isinstance(node, Component) for node in nodes):
            return {node.id : node for node in nodes}
        else:
            raise ValueError(f"Invalid argument for prop 'nodes': {nodes}")

    @property
    def sockets(self):
        return tuple(list(self._sockets.values()))

    def render_to_socket(self, id, rendered):
        socket = self._sockets[id]
        before = socket.to_plotly_json().__repr__().__hash__()
        socket.children.children = rendered
        after = socket.to_plotly_json().__repr__().__hash__()
        if before == after:
            #return no_update
            print(f"Socket {socket.id} did not change")
            pass
        else:
            print(f"Socket {socket.id} has changed")
        self._sockets[id] = socket
        return self._sockets[id].children
        #return html.Div(id=f"_{socket.id}", children=self._sockets[id])

    def identity(self, node):
        return node

    def initialize_intervals(self):
        print(self.async_channels)
        print(self._sockets)
        intervals = [dcc.Interval(id=f'asyncchannel_{phase_length}',
                                  n_intervals=-1,
                                  interval=5000,
                                  **{"aria-targets": ' '.join([target.id for target in targets]),
                                  "aria-sockets" : ' '.join([f"{self._sockets[target.id].id}" for target in targets])})
                                                    for phase_length, targets in self.async_channels.items()]
        return intervals

    def set_initial_layout(self):

        layout = [dbc.Container(
            id="root", children=self.sockets, style={"marginTop": "61.8px"}
        ), *self.intervals]

        return html.Div(children=layout, id='app')

    def acquire_targets(self):
        targets = {"input": [], "state": []}
        for id, node in self.nodes.items():
            available_props = set(node.available_properties)
            print(f"Node {id} has props: {available_props}")
            trigger_props = available_props.intersection(set(self.trigger_props.keys()))
            observable_props = available_props.intersection(set(self.mutable_props.keys()))
            required_props = {'value': ''}
            targets['state'].extend([(id, prop) for prop in observable_props])
            targets['input'].extend([(id, prop) for prop in trigger_props])
            for prop in observable_props:
                # print(f"hasattr({node.id}, {prop})? {hasattr(node, prop)}")
                if not hasattr(node, prop):
                    print(f"Setting {id}.{prop} to {self.mutable_props[prop]}")
                    setattr(node, prop, self.mutable_props[prop])
            for prop in trigger_props:
                if not hasattr(node, prop):
                    print(f"Setting {id}.{prop} to {self.trigger_props[prop]}")
                    setattr(node, prop, self.trigger_props[prop])

            # for prop, default_value in required_props.items():
            #     if not hasattr(node, prop):
            #         print(f"Setting {id}.{prop} to {default_value}")
            #         setattr(node, prop, default_value)

            if 'debounce' in observable_props:
                node.debounce = True
        return targets

    def acquire_async_targets(self):
        intervals = defaultdict(list)
        for id, node in self.nodes.items():
            if not hasattr(node, 'async_transformers'):
                continue
            elif not hasattr(node, 'interval'):
                node.interval = 1000
                
            if node.interval and isinstance(node.interval, (int, float)):
                intervals[node.interval].append(node)
            else:
                raise ValueError(
                    f"{id}.interval has an invalid value. (Got: {node.interval}; Expected: int or float > 0)")
        return intervals

    def resolve_generic_target(self, prop_name):
        d = defaultdict(list)
        for id, node in self.nodes.items():
            if not hasattr(node, prop_name):
                continue
            vals = getattr(node, prop_name).strip()
            for tx in vals.split():
                val = tx.strip()
                if not val:
                    continue
                if not hasattr(self, val):
                    raise RuntimeError(f"{prop_name} '{val}' not found!")
                else:
                    d[id].append(getattr(self, val))
        return d

    def resolve_transformers(self):
        return self.resolve_generic_target('className')
    def resolve_async_transformers(self):
        return self.resolve_generic_target('async_transformers')
    def resolve_renderers(self):
        return self.resolve_generic_target('renderers')

    def resolve_click_handlers(self):
        return self.resolve_generic_target('on_click')

    def render(self):
        rendered = []
        for id, node in self.nodes.items():
            #before = node.to_plotly_json()
            _node = node
            for tx in self.renderers[id]:
                _node = tx(_node)
            #after = node.to_plotly_json()
            #if before == after:
            #    rendered.append(no_update)
            #else:
            rendered.append(self.render_to_socket(id, _node))
        return rendered

    def apply_transformers(self):
        for id, node in self.nodes.items():
            print(f"Transforming {node.id}")
            if node and id in self.transformers:
                for tx in self.transformers[id]:
                    node = tx(node)
                self.nodes[id] = node
        return self.nodes

    def fire_onclick_handlers(self, mutations):
        print(f"Firing onclick handlers for {mutations}")
        for id, prop in mutations:
            if prop == 'n_clicks' and self.click_handlers[id]:
                for handler in self.click_handlers[id]:
                    print(f"Firing onClick handler for node {id}: {handler.__name__}")
                    handler()
                    print(f"Finished executing onClick handler for node {id}: {handler.__name__}")

    def generate_callback(self):
        output_deps = [dash.dependencies.Output(sock.children.id, 'children') for sock in self.sockets]
        input_deps = [dash.dependencies.Input(*target) for target in self.targets['input']]
        state_deps = [dash.dependencies.State(*target) for target in self.targets['state']]
        targets = self.targets['input'] + self.targets['state']
        for k, v in locals().items():
            print(red(k))
            print(cyan(v.__repr__()))

        @self.app.callback(output_deps,
                           input_deps,
                           state_deps)
        def update_state(*args, **kwargs):
            # print(f"Args: {args}\nKwargs: {kwargs}")
            # print(locals())
            state = {k:v for k,v in zip(targets, args) if not isinstance(v, (list, tuple))}
            print(f"Callback fired!")
            print(f"States: {state}")
            before_and_after = defaultdict(lambda: (None, None))
            mutations = []
            for k,v in state.items():
                id, prop = k
                print(f"{cyan(id)}.{green(prop)} :: {blue(v)}")
                try:
                    pre = getattr(self.nodes[id], prop)
                except:
                    pre = None
                post = k
                before_and_after[k] = (pre, post)
                if pre != post:
                    mutations.append(k)
                    setattr(self.nodes[id], prop, post)
                    print(f"{id}.{prop} has changed! (Was: {pre}; Now: {post})")
            # try:
            #     triggers = dash.callback_context.triggered
            #     possible_mutations = [([d['value'], *d['prop_id'].split(".")]) for d in triggers]
            # except:
            #     triggers = self.targets['input'] + self.targets['state']
            #     possible_mutations = [(getattr(self.nodes[id], prop), id, prop) for id, prop in triggers]
            #
            # print(triggers)
            # actual_mutations = []
            # for value, id, prop in possible_mutations:
            #     before = getattr(self.nodes[id], prop)
            #     if before == value:
            #         print(f"{id}.{prop} did not change, even though it's listed as a trigger in the callback context")
            #         continue
            #     else:
            #         print(f"{id}.{prop} changed to {value} (Was: {getattr(self.nodes[id], prop)})")
            #         actual_mutations.append((id, prop))
            #         setattr(self.nodes[id], prop, value)
            # if not actual_mutations:
            #     print(f"No mutations.")
            #     raise PreventUpdate
            #
            # else:
            if mutations:
                self.apply_transformers()
                self.fire_onclick_handlers(mutations)
                rendered = [node.children for node in self.render()]
                print(f"Rendered:")
                print(rendered)
                return rendered
            else:
                raise PreventUpdate

    def apply_async_transformers(self, node):
        for tx in self.async_transformers[node.id]:
            node = tx(node)
        return node

    def generate_async_callbacks(self):
        for timer in self.intervals:
            print(timer.__dict__)
            socks = getattr(timer, 'aria-sockets').split(" ")
            input_deps = [dash.dependencies.Input(timer.id, 'n_intervals')]
            output_deps = [dash.dependencies.Output(f"{sock_id}", 'children') for sock_id in socks]

            # state_deps = [dash.dependencies.State(sock_id, 'children') for sock_id in socks]
            for k,v in locals().items():
                print(red(k))
                print(cyan(v.__repr__()))
            targets = [self.nodes[id] for id in getattr(timer, 'aria-targets').split(" ")]
            @self.app.callback(output_deps, input_deps)
            def update_channel(_):
                print(f"Updating channel {timer.id}...")
                start = datetime.datetime.now()

                updated = [self.render_to_socket(target.id, self.apply_async_transformers(target))
                           for target in targets]
                stop = datetime.datetime.now()
                dt = (stop - start).microseconds
                print(f"""{timer.id:<20} :: Fired @ {datetime.datetime.now().strftime('%I:%M:%S.%f %p')}\n{timer.id:<20} :: Finished in {dt}μs.""")
                return updated



