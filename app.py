from tokamak.asyncmodels import Reactor
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash

external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    dbc.themes.BOOTSTRAP,
    dbc.themes.LUX,
]

app = dash.Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
    serve_locally=True,
    include_assets_files=True,
)

nodes = [dbc.Input(id='foo', type='number', value=0),
         # dcc.Interval(id='baz', interval=1000),
         dbc.Input(id='bar', type='number', value=0),
         html.Div(id='foobar', children=[html.H1(f"Sum is: 0")], async_transformers='update_sum')]

class App(Reactor):
    def __init__(self, app, nodes):
        #self.nodes = {node.id: node for node in nodes}
        self.nodelist = nodes
        super().__init__(app, nodes)
    def update_sum(self, node):
        print(f"Updating sum")
        the_sum = self.nodes['foo'].value + self.nodes['bar'].value
        print(f"It's {self.nodes['foo'].value} + {self.nodes['bar'].value} = {the_sum}")
        node.children = [html.H1(f"Sum is: {the_sum}")]
        print(node)
        return node


app_state = App(app, nodes)
# @app_state.app.callback(dash.dependencies.Output('foobar', 'children'),
#                         [dash.dependencies.Input('baz', 'n_intervals')])
# def update(_, app_state=app_state):
#     print(f"Fired!")
#     return html.H1(f"Sum is: {app_state.nodes['foo'].value + app_state.nodes['bar'].value}")
server = app_state.app.server
#
print(app.layout)
# start_server = input(f"Start the server now? (y/n) :")
# if start_server.strip().lower().startswith('y'):
#     app_state.app.run_server(port=8001)
