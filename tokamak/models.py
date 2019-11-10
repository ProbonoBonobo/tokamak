import dash_bootstrap_components as dbc
from dash.dependencies import ClientsideFunction
import random
from functools import partial
from collections import defaultdict, deque, OrderedDict, Counter
import inspect
import dash_core_components as dcc
from dash import no_update
import dash_html_components as html
import datetime
from gemeinsprache.utils import *
from rube.utils import pp, pidofport
import dash
from multiprocessing import RLock
from dash.development.base_component import Component
from typing import Tuple
from flask_caching import Cache

external_stylesheets = [dbc.themes.LUX]
DEBUG = True



watchlist = []
ignored = []
_cache = {}
_exec_times = defaultdict(float)
_mtimes = defaultdict(lambda: datetime.datetime.fromordinal(1))


def transformer(func):
    funcname = func.__name__
    print(f"{funcname} args:")
    pp(vars())
    def wrapped(*args, **kwargs):
        value = func(*args, **kwargs)
        return value

    return wrapped


class IndexedDict(OrderedDict):
    """Like an OrderedDict, which it extends with an `index` method for checking the numeric index
       of a key or value in its contents."""
    def __init__(self, mapping):

        super().__init__(mapping)

    @property
    def _id_seq(self):
        """List of keys. Generated dynamically to ensure it's always up-to-date."""
        return list(self.keys())

    @property
    def _node_seq(self):
        """List of values. Generated dynamically to ensure it's always up-to-date."""
        return list(self.values())

    def index(self, node_or_id: (Component, str)):
        try:
            if isinstance(node_or_id, str):  # it's an id
                _id = node_or_id
                _ord = self._id_seq.index(id)
            else:  # it's a component object
                _node = node_or_id
                # ...and because I am a Paranoid Parrot, I fear the potential for confusion if we return
                # an index based on value equality (a == b) that does not, in fact, recognize the argument
                # as being materially equal (a is b) to the indexed referent. Such behavior could lead Reactor
                # subclasses to mistakenly believe that a node stored in the child's own state is in fact being
                # passed to the browser, when in reality those nodes are beyond the purview of the event loop
                # that "pumps" state updates to the browser. That antipattern should probably be actively
                # guarded against.
                # One idea would be to introduce a bespoke Singleton metaclass applied directly
                # to the Component superclass to ensure objects with the same id are never created more than
                # once: see recipe 9.13, "Using metaclasses to control instance creation", from David Beazley's
                # Python Cookbook (https://github.com/dabeaz/python-cookbook/blob/master/src/9/using_metaclasses_to_control_instance_creation/example3.py).
                #
                # ...but in the meantime, we can suppress that behavior by first passing over the array of
                # nodes with a hash comparison operation.

                _ord = list(
                    map(lambda item, node=_node: 1 if item is node else 0, self._node_seq)
                ).index(1)
        except Exception as e:
            raise IndexError(f"Invalid index: {node_or_id} raised {e.__class__.__name} :: {e}")

        return _ord

    def __contains__(self, item):
        if isinstance(item, str):
            ans = item in self
        elif isinstance(item, Component):
            ans = item in self._node_seq and self.index(item)
        return ans

    def __getitem__(self, item: (int, str)):
        if isinstance(item, int):
            _id = self._id_seq[item]
            result = self[_id]
        else:
            try:
                result = super().__getitem__(item)
            except Exception as e:
                print(f"Can't get item {item}: {e.__class__.__name__} :: {e}")
                result = e
        return result


    def __getattr__(self, item):
        if item and not item.startswith("_"):
            try:
                node = self.__getitem__(item)
            except Exception as e:
                print(f'Cant get item {item} from dict: {e.__class__.__name__} :: {e}')
                node = super().__getattribute__(item)
        else:
            node = super().__getattribute__(item)
        return node




def default_props(argmap):
    def add_missing_defaults(nodes):
        nodes = {node.id: node for node in nodes}
        for id, node in nodes.items():
            missing_keys = argmap.keys() - nodes.keys()
            if missing_keys:
                for k in missing_keys:
                    value = argmap[k](node) if callable(argmap[k]) else argmap[k]
                    setattr(nodes[id], k, value)

        return nodes

    def outer(func):
        def inner(*args, **kwargs):
            return add_missing_defaults(func(*args, **kwargs))

        return inner

    return outer


#
# def transformer2(*args):
#     log_func_call_args = not bool(args)
#     triggers = args
#     print(cyan('Transformer call args:'))
#     pp(vars())
#
#     def _wrapped(func):
#         funcname = func.__name__
#         print(f"Hello")
#         # @functools.wraps
#
#         def maybe_cache(self, node, *args, **kwargs):
#             pp(_exec_times)
#             modified = _mtimes[funcname]
#             use_cache = any(_mtimes[trigger] > modified for trigger in triggers)
#
#             print(f"Execution of function {funcname} takes up to {_exec_times[funcname]}um")
#             print(f"Function {funcname} with triggers {triggers}:")
#             for trigger in triggers:
#                 print(green(f"{trigger:>24} :: {_mtimes[trigger]}"))
#
#             # @functools.wraps
#             def wrapped_tx():
#                 start = datetime.datetime.now()
#                 is_cached = False
#                 k = None
#                 if use_cache:
#                     print("Using cache")
#                     _hash = str(node).__hash__()
#                     _id = node.id
#                     k = (funcname, _hash)
#                     is_cached = k in _cache
#                 else:
#                     time.sleep(random.randrange(0,100000) * 0.000001)
#                 if is_cached:
#                     print(f"{funcname}({k}) using cached value... ({_cache[k]}")
#                     value = _cache[k]
#                 else:
#                     value = func(self, node, *args, **kwargs)
#                 if use_cache:
#                     _cache[k] = value
#                 finish = datetime.datetime.now()
#                 return value, (finish - start).microseconds, finish
#             output, exec_time, end_time = wrapped_tx()
#             _exec_times[funcname] = max(_exec_times[funcname], exec_time)
#             _mtimes[funcname] = end_time
#             print(f"Finished executing in {exec_time}us.")
#             return output
#         return maybe_cache
#     return _wrapped


class Reactor(object):

    _cache = {}
    _id = 0
    _exec_times = defaultdict(float)

    def __init__(self, app, nodes):
        if hasattr(self, "nodes"):
            raise RuntimeError(
                red(
                    f"Objects subclassed from UI mustn't set a 'nodes' attribute, or "
                    f"the superclass will break."
                )
            )
        if hasattr(self, "classmap"):
            raise RuntimeError(
                red(
                    f"Objects subclassed from UI mustn't set a 'classmap' attribute, but {self.__class__.__name__} does."
                )
            )
        # nodes = self._assign_keys_to_children(nodes)
        self._id += 1
        self.DEBUG = DEBUG
        self.nodes = IndexedDict({node.id: node for node in nodes} if not isinstance(nodes, dict) else nodes)
        self.nodes['appstate'] = dcc.Store(id='appstate', storage_type='local', state={
            'id': self._id,
            'targets': self.targets
        })
        self.nodes['eventloop'] = dcc.Interval(id='eventloop', interval=1000),
        self.classmap = {}
        self.renderers = {}
        self.semaphores = {}
        self.pending = {}
        self._batched_callback = None

        for id, node in self.nodes.items():
            # 1. Index the node by id in the class object's 'nodes' dictionary
            #    We stick this on the class instead of the instance because it may later prove best to
            #    reinitialize this object whenever there's a state update. (It's a strategy I've seen
            #    libraries with similar aspirations use.)

            self.semaphores[id] = RLock()
            self.pending[id] = defaultdict(deque)
            if not hasattr(node, "renderer") or not node.renderer:
                self.renderers[id] = self.identity
            else:
                name = node.renderer
                is_valid_renderer, render_f, err = self.validate_renderer(node)
                if is_valid_renderer:
                    self.renderers[id] = render_f
                    # self.nodes[id].renderer = render_f
                else:
                    raise RuntimeError(
                        f"Component {id} declares an invalid rendering function: {name} ({err})"
                    )
            methods = []
            if hasattr(node, "className") and isinstance(node.className, str):
                classlist = re.split(r"\s+", node.className)

                for klazz in classlist:
                    """"""
                    transformer_is_valid, transformer, err = self.validate_transformer(
                        node, klazz
                    )

                    if not transformer_is_valid:
                        print(RuntimeError(err))
                        # breakpoint()
                    methods.append(transformer)

                    # if self.DEBUG:
                    #         print(
                    #             f"Class {blue(klazz)} of {green(node.id)} doesn't resolve to a callback function accessible to the UI object. Is this a mistake?"
                    #         )
                    #         error_msg = red(
                    #             "Attempted to resolve class '{klazz}' to a UI method while registering callbacks for node {node.id}. Did you forget to define a '{klazz}' method? Full error below: \n\n {e}"
                    #             .format_map({
                    #                 'klazz': klazz,
                    #                 'node': node,
                    #                 'e': e
                    #             }))
                    #         print(error_msg)
                    #         # meth = lambda node, error=error_msg: print(error)
                    #         # methods.append(meth)
            #
            # except:
            #     # if the node has no callbacks, method list is the empty list
            #     methods = []
            print(node)
            try:
                self.classmap[node.id] = methods
            except:
                pass
        app = self._set_initial_layout(app)
        self._generate_callbacks(app)


        @app.callback(*self._callback_dependencies)
        # @cache.memoize(timeout=2)
        def callback(*args):
            return self._batched_callback(*args)

    def validate_transformer(self, node, tx_name):
        name = tx_name
        transformer = self.identity
        valid = False
        err = None
        if hasattr(self, name):
            transformer = getattr(self, name)
            if callable(transformer):
                sig = inspect.getfullargspec(transformer)
                arity = len(
                    [
                        arg
                        for arg in inspect.getfullargspec(transformer).args
                        if arg != "self"
                    ]
                )
                has_generic_signature = sig.varargs and sig.varkw
                if not has_generic_signature:
                    args, kwargs = [], dict(zip(inspect.getfullargspec(transformer).args[1:], [node]))
                else:
                    args, kwargs = [node], {}

                if arity == 1 or has_generic_signature:
                    before = node
                    args
                    try:
                        after = transformer(*args, **kwargs)
                    except Exception as e:
                        after = None
                        err = f"Transformer '{tx_name}' correctly resolved to a unary method, but when called with args {args} it raised a {e.__class__.__name__}: {e}"

                    valid = isinstance(
                        after, dash.development.base_component.Component
                    ) and type(before) == type(after)
                    err = (
                        err
                        if err
                        else f"Transformer '{tx_name}' correctly resolved to a unary method, but when called with args {args} it returned the wrong type (Expected: {type(before).__class__.__name__}; Got: {type(after).__class__.__name__})"
                    )
                else:
                    err = f"Transformer '{tx_name}' resolved to a method with an incorrect function signature: {inspect.getfullargspec(transformer)}  (Expected function arity of 1; Got {arity})"
            else:
                err = f"Transformer '{tx_name}' resolved to a non-callable attribute of {self} (Expected a callable object; got {type(transformer).__class__.__name__})"
        else:
            err = f"Transformer '{tx_name}' could not be resolved. Did you forget to define a {self.__class__.__name__}.{tx_name} method?"

        if not valid:
            transformer = self.identity
        return valid, transformer, err

    def validate_renderer(self, node):
        name = node.renderer
        renderer = self.identity
        valid = False
        err = None
        if hasattr(self, name):
            renderer = getattr(self, name)

            if callable(renderer):
                arity = len(
                    [
                        arg
                        for arg in inspect.getfullargspec(renderer).args
                        if arg != "self"
                    ]
                )
                if arity == 1:
                    args = dict(zip(inspect.getfullargspec(renderer).args[1:], [node]))
                    before = node
                    try:
                        after = renderer(before)
                    except Exception as e:
                        after = None
                        err = f"Renderer '{name}' correctly resolved to a unary method, but when called with args \n\n{args}\n\n it raised a(n) {e.__class__.__name__}: {e}"

                    valid = isinstance(after, dash.development.base_component.Component)
                    err = (
                        err
                        if err
                        else f"Renderer '{name}' correctly resolved to a unary method, but when called with args\n\n{args}\n\nit returned an object of the wrong type (Expected: instance of dash.development.base_component.Component; Got: {type(after)})"
                    )
                else:
                    err = f"Renderer '{name}' resolved to a method with an incorrect function signature: {inspect.getfullargspec(renderer)}  (Expected function arity of 1; Got {arity})"
            else:
                err = f"Renderer '{name}' resolved to a non-callable attribute of {self} (Expected a callable object; got {type(renderer)})"
        else:
            err = f"Renderer '{name}' could not be resolved. Did you forget to define a {self.__class__.__name__}.{renderer} method?"
        if not valid:
            renderer = self.identity
        return valid, renderer, err

    def identity(self, node):
        return node

    @staticmethod
    def _assign_keys_to_children(nodes):
        keys = list(
            node.key for node in filter(lambda node: hasattr(node, "key"), nodes)
        )
        duplicate_keys = set(
            key for key, occurrences in Counter(keys).items() if occurrences > 1
        )

        seen = set(keys)
        for i, node in enumerate(nodes):
            if hasattr(node, "key"):
                if node.key not in duplicate_keys:
                    continue
            _key = None
            while not _key:
                hexes = "0123456789ABCDEF"
                random_key = hexes[i % 16] + "".join(random.sample(hexes, 3))
                if random_key not in seen:
                    _key = random_key
            node.key = _key
        return nodes

    def _set_initial_layout(self, app):
        app.layout = html.Div(
            [
                dbc.NavbarSimple(
                    children=[
                        dbc.NavItem(dbc.NavLink("Link", href="#")),
                        dbc.DropdownMenu(
                            nav=True,
                            in_navbar=True,
                            label="Menu",
                            children=[
                                dbc.DropdownMenuItem("Entry 1"),
                                dbc.DropdownMenuItem("Entry 2"),
                                dbc.DropdownMenuItem(divider=True),
                                dbc.DropdownMenuItem("Entry 3"),
                            ],
                        ),
                    ],
                    brand="Interference Generator",
                    brand_href="#",
                    sticky="top",
                    color="dark",
                    dark=True,
                    style={"color": "#EEEEEE"},
                ),

                self.nodes.eventloop[0],
                dbc.Container(
                    id="approot", children=self.view, style={"marginTop": "61.8px"}
                ),
                html.P(id='targets', children=[','.join(target) for target in self.targets]),
                self.nodes.appstate,
            ]
        )
        return app

    def _generate_callbacks(self, app):
        def _update_state(state, targets=None, app_state=None, DEBUG=None):
            # print('Updating')
            print(f"_update_state got args:")
            pp(vars())
            has_update = False
            for target, value in state.items():

                id, prop = target.split(",")
                curr = getattr(app_state.nodes[id], prop)
                if curr != value and value != 'no_update':
                    has_update = True
                    app_state.submit_update(id, prop, value)
            if not has_update:
                return no_update
            has_update, updated_view = app_state.update_nodes()
            # try:
            #     json.dumps(updated_view)
            # except Exception as e:
            #     print(f"Couldn't serialize view: {updated_view}")
            if watchlist:
                print(red("============= End of Update ==============="))
                print(cyan("Watched node ids: ") + yellow(watchlist))
                for node_id in watchlist:
                    node = app_state.nodes[node_id]

                    # pp(node.to_plotly_json())

            return updated_view

        _scoped = partial(
            _update_state,  app_state=self, DEBUG=self.DEBUG
        )

        def batched_callback(args):
            return _scoped(args)

        self._batched_callback = batched_callback
        self._callback_dependencies = (
            dash.dependencies.Output("approot", "children"),
            [dash.dependencies.Input("appstate", "state")]
        )
        app.clientside_callback(
            ClientsideFunction(
                namespace='clientside',
                function_name='display'
            ),
            dash.dependencies.Output('appstate', 'state'),
            [dash.dependencies.Input('eventloop', 'n_intervals')],
            [dash.dependencies.State('targets', 'children'), *[dash.dependencies.State(*target) for target in self.targets]]
        )

    def to_plotly_json(self, node):
        try:
            ser = node.to_plotly_json()
        except TypeError as e:
            print(red(f"TypeError while serializing {node.id}: {e}"))
            print(node)
            # breakpoint()
        return ser

    def iter_targets(self):
        immutable_attrs = {
            "id",
            "key",
            "type",
            "className",
            "props",
            "namespace",
            "_namespace",
            "_type",
            "_prop_names",
            "_valid_wildcard_attributes",
            "available_properties",
            "available_wildcard_properties",
            "DYNAMIC_PROPS",
            "func_params",
            "valid_wildcard_attributes",
            "renderer",
            "label",
            "inverse",
        }
        immutable_ids = ['appstate', 'approot', 'eventloop', 'targets']
        for id, node in self.nodes.items():
            if id in immutable_ids:
                continue
            if isinstance(node, tuple):
                # yield ('interval_component', 'n_intervals')
                continue
            for attr in node.__dict__.keys():
                if attr not in immutable_attrs:
                    yield (id, attr)

    @property
    def targets(self):
        return list(self.iter_targets())

    def submit_update(self, id, prop, value):
        self.pending[id][prop].append(value)

    def update_nodes(self):
        has_update = False
        for id, node in self.nodes.items():
            if not isinstance(node, Component):
                continue
            component_updates = [(k, v[-1]) for k, v in self.pending[id].items() if len(v)]

            component_has_updates = len(component_updates)
            DEBUG = self.DEBUG and id not in ignored

            if hasattr(node, 'id'):
                if self.semaphores[id].acquire():
                    changed_props = []
                    msg = ""
                    if DEBUG:
                        print(yellow(f"{'[ACQUIRED]':>16}") + grey("  ::  "), end="")
                        print(
                            cyan(node.id),
                            white(f"locked by"),
                            cyan("BROWSER"),
                            f"pending updates to {component_has_updates} props: {magenta(list(dict(component_updates).keys()))} {component_updates})",
                        )
                        # if component_has_updates:
                        #     pp(dict(component_updates))
                    # if component_has_updates:
                    for prop, updates in self.pending[id].items():
                        prev = getattr(node, prop)
                        try:
                            next = updates.pop()
                            if next != prev:
                                changed_props.append((prop, next))
                            setattr(node, prop, next)
                        except:
                            next = prev
                        if DEBUG:
                            msg = f"{id}.{prop} (=> {prev}) has {len(updates)} pending updates: {list(updates)}"
                        if not updates:
                            if DEBUG:
                                print(grey(msg))
                            continue
                        else:
                            print(green(msg), yellow(f"(Setting to {next}!)"))
                        while updates:
                            updates.popleft()
                    if DEBUG:
                        changed_props = dict(changed_props)
                        print(green(f"{'[RELEASED]':>16}") + grey("  ::  "), end="")
                        print(
                            cyan(node.id),
                            f"modified {magenta(len(list(changed_props.keys())))} properties. ({magenta(list(changed_props.keys()))}) ({changed_props})",
                        )
                        if (
                            "aria-hidden" in changed_props
                            and getattr(node, "aria-hidden") is None
                        ):
                            setattr(node, "aria-hidden", "1")
                        # if changed_props:
                        #     pp(changed_props)
                    self.nodes[node.id] = node
                    _mtimes[node.id] = datetime.datetime.now()
                self.semaphores[id].release()

            component_has_update, updated_node, state_before, state_after = self.invoke_bidirectional_transformer(
                node
            )
            has_update = has_update or component_has_update
            if component_has_update and DEBUG:
                print(
                    f"\n ================= Node {green(id)} has updated ================== "
                )
                print(f"\n{green('Before:')}")
                pp(json.loads(state_before))
                print(green("\n\nAfter:"))
                pp(json.loads(state_after))
                print(
                    f"\n ================= Node {green(id)} has updated ================== "
                )
        return has_update, self.view

    def invoke_bidirectional_transformer(
        self, node
    ) -> Tuple[bool, Component, str, str]:
        """Iterate through the node's html class names. If the name of the class matches
           one of my methods, apply it. Then, compare the serialized representation of the node
           before and after transformation. Return the previous state, post-update state, and
           a boolean value indicating whether the states are different."""
        has_update = False
        before = None
        try:
            before = json.dumps(self.to_plotly_json(node)["props"], default=str)
        except TypeError as e:
            print(
                red(
                    f"Trouble serializing node {node.id} ({str(node)})\nGot TypeError: {e}"
                )
            )
        finally:
            after = before
        txnode = node
        needs_update = len(self.classmap[node.id])
        DEBUG = self.DEBUG and node.id not in ignored

        if needs_update:
            if self.semaphores[node.id].acquire():

                for tx in self.classmap[node.id]:
                    try:
                        txnode = tx(txnode)
                    except AttributeError as e:
                        # Probably just a formatting option, move along
                        print(f"Got an attribute error: {e}. Not important, right?")
                        pass
                    except Exception as e:
                        print(f"Got an unknown error: {e}. Not important, right?")
                try:
                    after = json.dumps(
                        self.to_plotly_json(txnode)["props"], default=str
                    )
                except TypeError as e:
                    print(
                        red(
                            f"Trouble serializing node {node.id} ({str(node)})\nGot TypeError: {e}"
                        )
                    )
                has_update = before != after
                before_dict, after_dict = None, None
                changed_props = {}
                if has_update:
                    before_dict = json.loads(before)
                    after_dict = json.loads(after)
                    print(f"Before dict: {before_dict}")
                    changed_props = {
                        k: v
                        for k, v in before_dict.items()
                        if k not in after_dict or v != after_dict[k]
                    }
                    if DEBUG:
                        print(yellow(f"{'[ACQUIRED]':>16}") + grey("  ::  "), end="")
                        print(
                            cyan(node.id),
                            f"locked by",
                            cyan("TRANSFORMER"),
                            f"pending {len(list(self.classmap[node.id]))} state transformations: {[meth.__name__ for meth in self.classmap[node.id]]}",
                        )
                        print(green(f"{'[RELEASED]':>16}") + grey("  ::  "), end="")
                        print(
                            cyan(node.id),
                            f"modified {magenta(len(list(changed_props.keys())))} properties. ({magenta(list(changed_props.keys()))})",
                        )
                self.semaphores[node.id].release()

            else:
                if DEBUG:
                    print(
                        red(node.id),
                        white(
                            f"could not be acquired. Its {len(list(self.classmap[node.id]))} pending updates ({self.classmap[node.id]}) will not be executed."
                        ),
                    )

        return has_update, txnode, before, after

    def inverse_of(self, klazz):
        return klazz

    def render(self, node):
        assert(node.id in self.renderers, f"No renderer found for node {node.id}!")
        assert(callable(self.renderers[node.id]), f"self.renderers[{node.id}] maps to a non-functional value: {self.renderers[node.id]} (Type: {type(self.renderers[node.id]).__name__})")

        # should this method accept some sort of conditional, bool-valued operator that determines whether a
        # particular component should be rendered?  This is probably a good idea in theory, but in practice it's
        # likely to violate React's assumption that nodes with indexical-looking keys (set by Dash itself,
        # I don't control the keys it sets on TreeContainer wrappers) refer to objects with a deterministic order. If
        # components can be omitted from the view, there's no longer a fixed ordering of #approot's TreeContainer
        # children. Perhaps open an issue on the Dash repository to use component ids instead of indexes when
        # setting TreeContainer keys.
        return self.renderers[node.id](node)

    @property
    def view(self):
        kids = [
            dbc.Container([dbc.Col(self.render(node))])
            for id, node in self.nodes.items()
        ]
        return kids

    def run_server(self, port=8081, debug=True, **kwargs):
        self.app.run_server(
            port=port, debug=debug, dev_tools_hot_reload=False, **kwargs
        )
