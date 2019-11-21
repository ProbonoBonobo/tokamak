import dash
import dash_bootstrap_components as dbc
from default_namespace.A import A
from default_namespace.MyComponent import MyComponent

app = dash.Dash(__name__)
app.layout = dbc.Jumbotron(A("testing"), MyComponent("hello world"))
