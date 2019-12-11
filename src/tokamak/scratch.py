import dash

try:
    # the try/except block is mainly to stay pep-8 compliant and avoid getting scolded about our import statements
    # being out-of-order
    from tokamak.install import apply_hotfixes

    apply_hotfixes()
except Exception as e:
    print(f"Error applying hotfixes: {e.__class__.__name__} :: {e}")

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

external_stylesheets = [dbc.themes.LUX]
DEBUG = True

foo = dbc.Input(id="foo", value="hello")
foo2 = dbc.Input(id="foo", value="hello world")
print(foo)
print(foo2)
print(foo == foo2)
print(foo.__dict__)
print(foo2.__dict__)
