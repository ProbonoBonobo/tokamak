from tokamak.models2 import Reactor
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
from dash import dash

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    include_assets_files=True,
)

app.config.suppress_callback_exceptions = True
server = app.server
app.layout = html.Div(id='approot', children=[])

class TodoApp(Reactor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def set_initial_layout(self):
        return html.Div(html.Section(id='todoapp', className='todoapp', children=[
            html.Header(id='header', className='header', children=html.Div(id='root', children=self.nodelist))
        ]))

if __name__ == '__main__':
    appstate = TodoApp()
    appstate.app.run_server(port=8080)
    pass
