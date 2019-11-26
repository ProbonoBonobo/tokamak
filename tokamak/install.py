"""
This installer does one thing only: it loads the filepath associated with
the dash.base_component submodule that defines the prototypical Component
object from which all Dash components inherit.  It evaluates the md5 hash
of the file.  If different from tokamak/base_component_override.py, then
the installer will overwrite the original definition with our own.

I have tried many, many, many alternatives, and none completely solve the
problem that I've experienced with modules that list dash as a dependency.
See open issue on pyenv repository: "Provide a way to allow explicit
overrides of subdependency versions of top level packages in pipfile"
(https://github.com/pypa/pipenv/issues/1921)

"""
import os
from hashlib import md5
from gemeinsprache.utils import *
from collections import deque
from tokamak.utils import logger
import inspect
log = logger('[ tokamak/install.py ]')


def get_content(fp, mode='r'):
    with open(fp, mode) as f:
        raw = f.read()
    return raw

def overwrite(fp, new_contents):
    hash_before = get_md5_hash(fp)
    with open(fp, 'w') as f:
        f.write(new_contents)
    hash_after = get_md5_hash(fp)
    has_changed = hash_before != hash_after
    log(f"Overwriting {os.path.basename(fp)}...")
    log(f"    Hash before: {hash_before}")
    log(f"     Hash after: {hash_after}")
    log(f"     Different?: {yellow('Yes') if has_changed else green('No')}")
    return hash_before, hash_after, has_changed

def get_md5_hash(fp):
    return md5(get_content(fp, 'rb')).hexdigest()


def apply_hotfixes():
    log("Loading dash.development.base_component...")
    from dash.development import base_component
    path_to_base_component = base_component.__file__
    path_to_base_component_override = os.path.join(os.path.dirname(__file__), "base_component_override.py")
    if not os.path.isfile(path_to_base_component_override):
        raise RuntimeError(f"A required file could not be located:                                              \n"
                           f"        {path_to_base_component_override}.                                         \n"
                           f"This file is required to modify Dash framework in order to make it possible to use Dash component "
                           f"objects as storage for distributed application state. Without this modification, the UI "
                           f"cannot launch because Dash enforces no common protocol regarding what constitutes a "
                           f"valid wildcard prefix (e.g., `aria-somecustomprop` will be allowed on components that "
                           f"explicitly define `aria` to be among the wildcard prefixes that greenlight a user-defined "
                           f"prop, but dash_bootstrap_components doesn't define this property, so none of its subclasses "
                           f"are runtime-extensible).")
    its_hash = get_md5_hash(path_to_base_component)
    required_hash = get_md5_hash(path_to_base_component_override)
    base_component_needs_override = bool(its_hash != required_hash)
    if not base_component_needs_override:
        return True
    color = red if base_component_needs_override else green
    log(f"    Resolved filepath: {path_to_base_component}")
    log(f"    Resolved md5 hash: {its_hash}")
    log(f"    Required md5 hash: {required_hash}")
    log(f"    Requires override: {color('Yes' if base_component_needs_override else 'No')}")
    if base_component_needs_override:
        new_contents = get_content(path_to_base_component_override)
        before, after, has_changed = overwrite(path_to_base_component, new_contents)
    from dash.development.base_component import Component
    source = inspect.getsource(Component)
    log(f"Source code of Component is now:")
    print(source)
    success = after == required_hash
    return success


if __name__ == '__main__':
    success = apply_hotfixes()
    if success:
        log("Installation successful.")
    else:
        log("Installation failed.", color=red)
