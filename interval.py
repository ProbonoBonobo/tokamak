import datetime

import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import plotly
from dash import no_update
from dash.dependencies import Input, Output
# from dash import no_update


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

import time

appstate = {"foo": 'hello', "bar": 'world'}
def render(appstate=appstate):
    return [dbc.Input(id='foo', value=appstate['foo']),
            dbc.Input(id='bar', value=appstate['bar'])]


app = dash.Dash('interval', external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.layout = html.Div(children=[
    dcc.Interval(id='interval', interval=1000),
    html.P(id='status', children='Last updated at:'),
    html.Div(children=render(), id='root')]
)



@app.callback(Output('root', 'children'),
              [Input('interval', 'n_intervals')])
def update_metrics(n):
    return render()

@app.callback(Output('status', 'children'),
              [Input('foo', 'value'), Input('bar', 'value')])
def update(foo, bar):
    if foo == appstate['foo'] and bar == appstate['bar']:
        return no_update

    appstate['foo'] = foo
    appstate['bar'] = bar
    return [html.P(f"Last updated at: {datetime.datetime.now().isoformat()}"),
    html.P(f"Context: {dash.callback_context.triggered}")]


if __name__ == '__main__':
    app.run_server(debug=False, port=8888)
