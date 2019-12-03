import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import datetime
from tokamak.install import apply_hotfixes
apply_hotfixes()
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': {
                'title': 'Dash Data Visualization'
            }
        }
    ),
    html.Div(id='root', children=[], **{'thisIsWeird' : 'hello'}),
    dbc.Button(id='hello', children='click me!')
])

@app.callback(dash.dependencies.Output('root', 'thisIsWeird'),
               [dash.dependencies.Input('hello', 'n_clicks')])
def say_hello(_):
    return f"Hello at {datetime.datetime.now().isoformat()}"



if __name__ == '__main__':
    app.run_server(debug=False, port=8060)