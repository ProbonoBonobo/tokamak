import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import ClientsideFunction, Input, Output, State
from tokamak.models import Reactor, transformer
root = [
    dcc.Input(id='input', value=''),
    dcc.Input(id='foo', value='')]
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div([
    html.Div(id='root', children=root),
    dcc.Interval(interval=1000, id='eventloop'),
    dcc.Input(id='targets', state={'value': [[k.id, 'value'] for k in root]}),
    dcc.Store(id='appstate', className='fire', state={}),
    html.Div(id='output-clientside', children=''),
    html.Div(id='output-serverside', children='')
])
class InterferenceGenerator(Reactor):
    def __init__(self, app, nodes):
        super().__init__(app, nodes)
    @transformer
    def fire(self, node):
        print(node)
        return node

#
@app.callback(
    Output('output-serverside', 'children'),
    [Input('appstate', 'state')])
def update_output(value):
    return 'Server says "{}"'.format(value)


app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='display'
    ),
    Output('appstate', 'state'),
    [Input('eventloop', 'n_intervals')],
    [State('targets', 'state'), State('input', 'value'), State('foo', 'value')]
)

if __name__ == "__main__":
    app.run_server(port=8070)