import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import ClientsideFunction, Input, Output, State
from tokamak.models import Reactor, transformer
root = [
    html.P(id='uuid', children=''),
    dcc.Input(id='input', value=''),
    dcc.Input(id='foo', value='')]
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div([
    html.Div(id='root', children=root),
    dcc.Interval(interval=60, id='eventloop'),
    dcc.Input(id='targets', state={'value': [[k.id, 'value'] for k in root]}),
    dcc.Store(id='appstate', className='fire', state={}),
    html.Div(id='output-clientside', children=[]),
    html.Div(id='output-serverside', children=[])
])
class InterferenceGenerator(Reactor):
    nodes = {}
    def __init__(self, app, nodes):
        super().__init__(app, nodes)

        self.nodes[] = self.nodes
    @transformer
    def fire(self, node):
        print(node)
        return node

#
import datetime
@app.callback(
    Output('output-serverside', 'children'),
    [Input('eventloop', 'n_intervals')])
def update_output(value):
    return f'Server says {datetime.datetime.now().isoformat()}'



app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_timer'
    ),
    Output('output-clientside', 'children'),
    [Input('eventloop', 'n_intervals')]
)

app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='uuid'
    ),
    Output('uuid', 'children'),
    [Input('eventloop', 'n_intervals')],
    [State('uuid', 'children')])



if __name__ == "__main__":
    app_state(app, )
    app.run_server(port=8070)