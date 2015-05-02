#!/usr/bin/env python

import os
import sys
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='nope',
    version='0.1.0',
    description='Statically type a subset of Python 3',
    long_description=read("README.rst"),
    author='Michael Williamson',
    author_email='mike@zwobble.org',
    url='http://github.com/mwilliamson/nope',
    packages=[
        'nope',
        'nope.inference',
        'nope.parser',
        'nope.platforms',
        'nope.platforms.nodejs',
        'nope.platforms.dotnet',
        'nope.types',
    ],
    scripts=['scripts/nope'],
    install_requires=[
        "funcparserlib==0.3.6",
        "dodge>=0.1.9,<0.2",
        "zuice>=0.3.0,<0.4",
    ],
    keywords="nope static type",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Operating System :: OS Independent',
    ],
)

