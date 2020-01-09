import dash

try:
    # the try/except block is mainly to stay pep-8 compliant and avoid getting scolded about our import statements
    # being out-of-order
    from tokamak.install import apply_hotfixes

    apply_hotfixes()
except Exception as e:
    print(f"Error applying hotfixes: {e.__class__.__name__} :: {e}")
import dash

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from functools import reduce

# from tokamak.models import Reactor, transformer, default_props
# from tokamak.utils import pidofport
import dash_bootstrap_components as dbc

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask_caching import Cache
from dash import no_update

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# cache = Cache(app.server, config={
#     # try 'filesystem' if you don't want to setup redis
#     'CACHE_TYPE': 'filesystem',
#     'CACHE_DIR': "/tmp"
# })
app.config.suppress_callback_exceptions = True
server = app.server


timeout = 20

from gemeinsprache.utils import red, green, cyan, yellow


def print_vals(*vals):
    def capture_vals():
        return [eval(val) for val in vals]

    def outer(func):
        def inner(*args, **kwargs):
            before = capture_vals()
            response = func(*args, **kwargs)
            after = capture_vals()
            for k, v1, v2 in zip(vals, before, after):
                print(f"{cyan(k):>24} :: Was: {yellow(before):<24} :: Now: {green(v2)}")

        return inner

    return outer


class TodoItem(dbc.ListGroupItem):
    data = {"counter": -1}

    def __getattr__(self, k):
        if k in self.data:
            return self.data[k]
        return super().__getattribute__(k)

    def __init__(self, *args, **kwargs):
        self.data["counter"] += 1
        self.key = str(self.data["counter"])
        super().__init__(*args, **kwargs)


from collections import defaultdict


class TodoFilter(dbc.Button):
    data = defaultdict(lambda: None)

    @property
    def n_clicks(self):
        n_clicks = self.data[self.id]
        return n_clicks

    @n_clicks.setter
    def n_clicks(self, value):
        self.data[self.id] = value
        return self.data[self.id]


class TodoItems(dbc.ListGroup):
    items = []

    def add(self, item):
        self.items.append(TodoItem(item))

    def remove(self, item):
        self.items.remove(item)

    @property
    def children(self):
        return self.items

    @children.setter
    def children(self, v):
        pass


class TodoApp(dbc.Jumbotron):
    items = TodoItems()
    context = None
    active_filter = "filter1"
    n_clicks = {"filter1": None, "filter2": None}

    @property
    def children(self):
        return [
            html.Section(children=str(self.context)),
            html.Section(
                className="todoapp",
                children=[
                    html.Header([
                        html.H1("todos"),
                        dbc.Input(
                            id="add-todo",
                            className="new-todo",
                            placeholder="What do you want to do today?",
                        )],
                        className="header"
                    ),
                    html.Section(html.Div(self.items), className="main"),
                    html.Footer(
                        [
                            html.Span(className="todo-count"),
                            html.Ul(
                                [
                                    TodoFilter(children="All", id="filter1", key="0"),
                                    TodoFilter(
                                        children="Active", id="filter2", key="1"
                                    ),
                                ],
                                className="filters",
                            ),
                        ]
                    ),
                ],
            ),
        ]


app.layout = html.Div(children=TodoApp(), id="root")


@app.callback(
    dash.dependencies.Output("root", "children"),
    [
        dash.dependencies.Input("add-todo", "n_submit"),
        dash.dependencies.Input("filter1", "n_clicks"),
        dash.dependencies.Input("filter2", "n_clicks"),
    ],
    [dash.dependencies.State("add-todo", "value")],
)
def callback(_, selected_filter1, selected_filter2, value):
    print(dash.callback_context.inputs)
    print(dash.callback_context.triggered)
    print(dash.callback_context.states)
    d = {
        k: getattr(dash.callback_context, k) for k in ("inputs", "triggered", "states")
    }
    changed_ids = [list(t.values())[0] for t in dash.callback_context.triggered]

    out = TodoApp(context=str(d))

    new_state = dict(
        (tuple(tup[0].split(".")), tup[1])
        for tup in [tuple(x.values()) for x in dash.callback_context.triggered]
    )
    if value:
        out.add(value)
    print(new_state)
    if "filter1" in changed_ids:
        out.n_clicks["filter1"] = selected_filter1
    elif "filter2" in changed_ids:
        out.n_clicks["filter2"] = selected_filter2
    out.n_clicks["filter1"]

    if all(
        TodoFilter(id=id.split(".")[0]).n_clicks == val
        for id, val in changed_ids
    ):
        return dash.no_update

    return out


if __name__ == "__main__":
    app.run_server(port=8000, debug=False)
