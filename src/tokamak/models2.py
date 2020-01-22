from collections import defaultdict
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash
import dash_html_components as html
from dash.development.base_component import Component
import json
import dash
from dash import callback_context
try:
    # the try/except block is mainly to stay pep-8 compliant and avoid getting scolded about our import statements
    # being out-of-order
    from tokamak.install import apply_hotfixes

    apply_hotfixes()
except Exception as e:
    print(f"Error applying hotfixes: {e.__class__.__name__} :: {e}")


required_props  = {'value': ''}

mutable_props   = {"value": '',
                      "on": False,
                      "n_clicks": -1,
                      "n_clicks_timestamp": -1,
                      "state": {},
                      "n_intervals": -1}

python_only_props = {"renderers",
                     "on_click"}

class Reactor:
    mutable_props = mutable_props
    required_props = required_props
    _external_stylesheets = [
            "https://codepen.io/chriddyp/pen/bWLwgP.css",
            dbc.themes.BOOTSTRAP,
            dbc.themes.LUX,
        ]
    def __init__(self, app=None, nodes={}, external_stylesheets=None, hide_navbar=False):
        self.nodes = nodes
        self.external_stylesheets = external_stylesheets or self._external_stylesheets
        self.hide_navbar = hide_navbar
        self.app = app or self._initialize_app()

        self.targets = self.acquire_targets()
        self.async_channels = self.acquire_async_targets()
        self.transformers = self.resolve_transformers()
        self.renderers = self.resolve_renderers()
        self.click_handlers = self.resolve_click_handlers()
        self.callback = self.generate_callback()


        self.app.layout = self.set_initial_layout()
    def _initialize_app(self):
        ns = {}
        init_str = """app = dash.Dash(
            __name__,
            external_stylesheets=self.external_stylesheets,
            suppress_callback_exceptions=True,
            include_assets_files=True,
        )
        
        # cache = Cache(app.server, config={
        #     # try 'filesystem' if you don't want to setup redis
        #     'CACHE_TYPE': 'redis',
        #     'CACHE_DIR': "/tmp"
        # })
app.config.suppress_callback_exceptions = True
server = app.server
app.layout = html.Div(id='approot', children=[])"""
        exec(init_str, globals(), locals())
        print(globals().keys())
        print(locals().keys())
        globals().update({'app': locals()['app'], 'server': locals()['server']})
        return locals()['app']

    def identity(self, node):
        return node

    def set_initial_layout(self):
        navbar = dbc.NavbarSimple(
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
        root = html.Div(
                id="root", children=self.render(), style={"marginTop": "61.8px"}
            )

        if self.hide_navbar:
            layout = [root]
        else:
            layout = [navbar, root]



        for id, node in self.nodes.items():
            if hasattr(node, 'async') and node.async:
                layout.append(node)
        return html.Div([dcc.Interval(id='eventloop',interval=500), *layout])

    def acquire_targets(self):
        targets = []
        for id, node in self.nodes.items():
            available_props = set(node.available_properties)
            observable_props = available_props.intersection(set(self.mutable_props.keys()))
            required_props = {'value': ''}
            targets.extend([(id, prop) for prop in observable_props])
            for prop in observable_props:
                # print(f"hasattr({node.id}, {prop})? {hasattr(node, prop)}")
                if not hasattr(node, prop):
                    setattr(node, prop, self.mutable_props[prop])
                    print(node)

            for prop, default_value in required_props.items():
                if not hasattr(node, prop):
                    setattr(node, prop, default_value)

            if 'debounce' in observable_props:
                node.debounce = True
        return targets

    def acquire_async_targets(self):
        intervals = defaultdict(list)
        for id, node in self.nodes.items():
            if not hasattr(node, 'interval'):
                continue
            elif node.interval and isinstance(node.interval, (int, float)):
                intervals[node.interval].append(node)
            else:
                raise ValueError(f"{id}.interval has an invalid value. (Got: {node.interval}; Expected: int or float > 0)")
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

    def resolve_renderers(self):
        return self.resolve_generic_target('renderers')


    def resolve_click_handlers(self):
        return self.resolve_generic_target('on_click')

    def render(self):
        rendered = []
        for id, node in self.nodes.items():
            for tx in self.renderers[id]:
                node = tx(node)
            rendered.append(node)
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
        @self.app.callback(dash.dependencies.Output('root', 'children'),
                           [dash.dependencies.Input(*target) for target in self.targets])
        def update_state(*args, app_state=self):
            # self.log(f"Callback fired!")
            possible_mutations = [([d['value'], *d['prop_id'].split(".")]) for d in dash.callback_context.triggered]
            # self.log(str(dash.callback_context.triggered))
            actual_mutations = []
            for value, id, prop in possible_mutations:
                before = getattr(self.nodes[id], prop)
                if before == value:
                    print(f"{id}.{prop} did not change, even though it's listed as a trigger in the callback context")
                    continue
                else:

                    self.log(f"{id}.{prop} changed to {value} (Was: {getattr(self.nodes[id], prop)})")
                    actual_mutations.append((id, prop))
                    setattr(self.nodes[id], prop, value)
            if not actual_mutations:
                print(f"No mutations.")
                raise PreventUpdate

            else:
                self.log(f"Detected {len(actual_mutations)} mutated props this cycle: {actual_mutations}")
                self.apply_transformers()
                self.fire_onclick_handlers(actual_mutations)
                rendered = self.render()

            return rendered

