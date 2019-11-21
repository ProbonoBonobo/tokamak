# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class A(Component):
    """An A component.


Keyword arguments:
- children (dict; optional): Children
- href (string; optional): The URL of a linked resource."""
    @_explicitize_args
    def __init__(self, children=None, href=Component.UNDEFINED, **kwargs):
        self._prop_names = ['children', 'href']
        self._type = 'A'
        self._namespace = 'default_namespace'
        self._valid_wildcard_attributes =            []
        self.available_properties = ['children', 'href']
        self.available_wildcard_properties =            []

        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        for k in []:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')
        super(A, self).__init__(children=children, **args)
