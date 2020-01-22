import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash
from dash import no_update

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
server = app.server
nodes = [dbc.Input(id='foo', type='text', value=0),
         # dcc.Interval(id='baz', interval=1000),
         dbc.Input(id='bar', type='text', value=0),
         html.Div(id='foobar', children=[html.H1(f"Sum is: 0")], async_transformers='update_sum'),
         dbc.Container(id='status_container', children=[html.Div(id='status', children=[])])]

app.layout = dbc.Container(children=[dcc.Interval(id='eventloop', interval=1000, n_intervals=-1),
                                     dbc.Row([dbc.Col([nodes[0]]),
                                              dbc.Col([nodes[1]])]),
                                     dbc.Row([dbc.Col([nodes[2]])]),
                                     dbc.Row([dbc.Col([nodes[3]])])])

@app.callback(dash.dependencies.Output('foobar', 'children'),
              [dash.dependencies.Input('foo', 'value'),
               dash.dependencies.Input('bar', 'value')])
def update_sum(foo, bar):
    print(f"Foo: {foo}, {type(foo).__name__}")
    # damn polymorphic argument types... casting is required to ensure 0s aren't treated as empty strings

    strfoo, strbar = str(foo), str(bar)
    intfoo, intbar = int(strfoo), int(strbar)
    if strfoo and strbar:
        return html.H1(f"Sum is: {intfoo + intbar}")
    return no_update

@app.callback(dash.dependencies.Output('status', 'children'),
              [dash.dependencies.Input('eventloop', 'n_intervals')],
              [dash.dependencies.State('status', 'children')])
def update_status(_, kids):
    print(f"Async callback fired {_} times")
    kids.append(html.P(f"Fired {_} times"))
    return kids

