from functools import reduce
from tokamak.models import Reactor, transformer, renderer, default_props
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
import dash_daq as daq


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
# cache = Cache(app.server, config={
#     # try 'filesystem' if you don't want to setup redis
#     'CACHE_TYPE': 'redis',
#     'CACHE_DIR': "/tmp"
# })
app.config.suppress_callback_exceptions = True
server = app.server

DEBUG = False