#!/usr/bin/env python

from distutils.core import setup

setup(name='tokamak',
      version='0.1.0',
      description='Dash wrapper for callback-free SPA apps',
      author='Kevin Zeidler',
      author_email='',
      url='',
      packages=['tokamak', 'interference'],
      package_dir={"tokamak": "src/tokamak",
                   "interference": "src/interference"}
     )
