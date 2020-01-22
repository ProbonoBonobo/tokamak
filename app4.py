import random
import time
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from collections import deque
import dash_html_components as html
import dash
from munch import Munch
from flask_caching import Cache
import os
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
cache = Cache(app.server, config={
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', '')
})

server = app.server
updates = []
app.state = Munch({"x": 0, "y": 0, "sum": 0, "log": []})

class BlockingUpdate(html.Div):
    def __init__(self, *args, **kwargs, ):

def render():
    global app
    state = app.state
    return [dbc.Row([dbc.Col(children=[dbc.Input(type='number', value=state.x, id='x')], width=6),
                     dbc.Col(children=[dbc.Input(type='number', value=state.y, id='y')], width=6)]),
            dbc.Row(dbc.Col(children=[html.H2(f"The sum is: {state.x + getattr(state, 'y')}")]))]

app.layout = html.Div(id='root', children=[     html.Div(id='intervals', children=[
                                                    dcc.Interval(id='eventloop', interval=2000)
                                                ]),
                                                dbc.Container(id='sync', children=render()),
                                                dbc.Container(id='async', children=[
                                                    html.Div(id='log', children=[html.P("Application loaded.")])]),
                                                ])

def to_int(val):
    return 0 if not val else int(val)

@app.callback(dash.dependencies.Output('sync', 'children'),
              [dash.dependencies.Input('x', 'value'), dash.dependencies.Input('y', 'value')])
@cache.memoize(timeout=1)
def update_state(x, y):
    # global app
    # app.state.log.appendleft(html.P(f"Updating sum..."))
    app.state.x = to_int(x)
    app.state.y = to_int(y)
    app.state.sum = to_int(app.state.x + app.state.y)
    # app.state.log.appendleft(html.P(f"Sum is now: {app.state.sum}"))
    return render()

@app.callback(dash.dependencies.Output('log', 'children'),
                  [dash.dependencies.Input('eventloop', 'n_intervals')])
# @cache.memoize(timeout=20)
def update_log(_):
    print(f"Async update fired at {time.time()} ({_})")
    updates.append((time.time(), _))
    msgs = ["Reticulating splines...",
            "Calculating cohomologies...",
            "Contemplating P vs. NP...",
            "Generating lie algebras...",
            "Initializing commutative rings...",
            "Waiting...",
            "Done.",
            "Done.",
            "Finished.",
            "No work to do. Going to sleep...",
            "No work to do. Going to sleep...",
            "Update complete.",
            "Update complete.",
            "Update complete."]
    app.state.log = [html.P(update.__repr__()) for update in updates]
    return list(app.state.log)


app.run_server(port=8050, debug=False)

