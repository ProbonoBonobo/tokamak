import dash
import dash_html_components as html
import datetime
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import time

app = dash.Dash(name=__name__)

app.layout = dbc.Container([dbc.Row([dbc.Col(dbc.Label("Client time is:"), width=2),
                                     dbc.Col(html.H2('', id='client-time'), width=10)]),
                            dbc.Row([dbc.Col(dbc.Label("Server time is:"), width=2),
                                     dbc.Col(html.H2('', id='server-time'), width=10)]),
                                     dcc.Interval(id='interval', interval=16, n_intervals=0)])

# using serverside callback
@app.callback(dash.dependencies.Output('server-time', 'children'),
              [dash.dependencies.Input('interval', 'n_intervals')])
def update_timer(_):
    return datetime.datetime.now().strftime("%c")

# using clientside callback (remember to create the clientside.js file in the assets folder!)
app.clientside_callback(
    dash.dependencies.ClientsideFunction(
        namespace='clientside',
        function_name='update_timer'
    ),
    dash.dependencies.Output('client-time', 'children'),
    [dash.dependencies.Input('interval', 'n_intervals')])


if __name__ == '__main__':
    app.run_server(port=8889)
