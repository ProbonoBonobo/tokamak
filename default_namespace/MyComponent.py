# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class MyComponent(Component):
    """A MyComponent component.
General component description.

Keyword arguments:
- children (dict; optional): Children
- foo (number; default 42): Description of prop foo.
- data-* (string; optional): Wildcard data
- aria-* (string; optional): Wildcard aria
- bar (default 21): Description of prop bar.
- baz (number | string; optional)"""
    @_explicitize_args
    def __init__(self, children=None, foo=Component.UNDEFINED, bar=Component.UNDEFINED, baz=Component.UNDEFINED, **kwargs):
        self._prop_names = ['children', 'foo', 'data-*', 'aria-*', 'bar', 'baz']
        self._type = 'MyComponent'
        self._namespace = 'default_namespace'
        self._valid_wildcard_attributes =            ['data-', 'aria-']
        self.available_properties = ['children', 'foo', 'data-*', 'aria-*', 'bar', 'baz']
        self.available_wildcard_properties =            ['data-', 'aria-']

        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        for k in []:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')
        super(MyComponent, self).__init__(children=children, **args)
