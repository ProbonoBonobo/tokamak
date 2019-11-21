from functools import reduce
# from tokamak.models import Reactor, transformer, default_props
# from tokamak.utils import pidofport
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from werkzeug.serving import WSGIRequestHandler
import json
import dash
import dash_daq as daq

from flask_caching import Cache
import dash_html_components as html
import os
import datetime
# from tokamak.models import transformer_v2, decorator_result
# from tokamak.models import to_serializable

import datetime
import os
import random
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask_caching import Cache
from dash import no_update

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
cache = Cache(app.server, config={
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': "/tmp"
})
app.config.suppress_callback_exceptions = True
server = app.server


timeout = 20
class State:
    def __init__(self):
        self.timer = datetime.datetime.now()
        self.time_color = "#ff3344"


    def render(self):
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1(id='clock', children=self.timer.isoformat(), style={"color": self.time_color})
                    ]),
                ]),
            dbc.Row([
                dbc.Col([
                    daq.ColorPicker(id='color_picker', value={"hex": self.time_color})
                ])
            ])
        ])

state = State()
app.layout = html.Div(
                      children=[dcc.Interval(id='interval', interval=100, n_intervals=0),
                       html.Div(id='root', children=State().render())])
@app.callback(dash.dependencies.Output('root', 'children'),
              [dash.dependencies.Input('interval', 'n_intervals'), dash.dependencies.Input('color_picker', 'value')])
def callback(_, color, state=state):
    state.time_color = color['hex']
    state.timer = datetime.datetime.now()
    # print(state.render())
    return state.render()



# app.run_server(port=8888, debug=True)

