#!/usr/bin/env python
"""
(Python >3.3, ptpython>=2.0.6)
Interactively run a python file from within the ptpython REPL and periodically
poll for changes. When a change is detected, the file will be reexecuted
automatically in the REPL's global scope. In the event that there's a syntax
error, the error traceback will be printed to the REPL.

Based on the example of embedding a Python REPL into an asyncio
application (see: https://github.com/prompt-toolkit/ptpython/blob/master/examples/asyncio-python-embed.py)
"""
from __future__ import unicode_literals
from ptpython.repl import embed
from concurrent.futures import ThreadPoolExecutor
import sys
import os
import asyncio
from collections import deque, defaultdict
import traceback
import argparse

parser = argparse.ArgumentParser(
    description="""Interactively launch a python application in a ptpython REPL and periodically poll for changes."""
)
parser.add_argument(dest="filepaths", metavar="filepaths", nargs="*")

state = defaultdict(lambda: deque([None, None]))
loop = asyncio.get_event_loop()


@asyncio.coroutine
def poll_for_changes(filepaths):
    """
    Coroutine that polls filepaths for changes. When a change is detected,
    its variable bindings will be loaded into the global scope and made
    available to the REPL.
    """
    while True:
        for filepath in filepaths:
            _hashes = state[filepath]
            with open(filepath, "r") as f:
                _hashes.append(f.read().__hash__())
                _hashes.popleft()
            before, after = _hashes
            if before != after:
                with open(filepath, "r") as f:
                    try:
                        exec(f.read(), globals())
                    except Exception as e:
                        print(f"{e.__class__.__name__} :: {e}")
                        traceback.print_exc(file=sys.stdout)
        yield from asyncio.sleep(1)


@asyncio.coroutine
def interactive_shell():
    """
    Coroutine that starts a Python REPL from which we can access the
    loaded application's state.
    """
    try:
        yield from embed(
            globals=globals(), return_asyncio_coroutine=True, patch_stdout=False
        )
    except EOFError:
        # Stop the loop when quitting the repl. (Ctrl-D press.)
        loop.stop()


def main(filepaths):
    asyncio.ensure_future(poll_for_changes(filepaths))
    asyncio.ensure_future(interactive_shell())

    loop.run_forever()
    loop.close()


if __name__ == "__main__":
    args = parser.parse_args()
    invalid_filepaths = [
        fp for fp in args.filepaths if not os.path.isfile(fp) or not fp.endswith(".py")
    ]
    if not args.filepaths:
        print(f"usage: ptpython_async.py [-h] [filepaths [filepaths ...]]")
        sys.exit(1)
    if invalid_filepaths:
        print(f"Invalid filepaths: {invalid_filepaths}")
        sys.exit(1)
    else:
        main(args.filepaths)
