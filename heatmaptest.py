import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import numpy as np

with open("/home/kz/projects/tokamak/apps/InterferenceGenerator/utils.py", "r") as f:
    exec(f.read())


def generate_table():
    zdata = np.array(eng.eval("input_fig")).tolist()
    fig = go.Heatmap(z=zdata)
    return dcc.Graph(figure={"data": [fig]})

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H4(children='Demo Heatmap'),
    generate_table()
])

if __name__ == '__main__':
    app.run_server(debug=True)
