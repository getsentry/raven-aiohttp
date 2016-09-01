#!/usr/bin/env python
"""
raven-aiohttp
=============

A transport for `raven-python <https://github.com/getsentry/raven-python>`_
which supports Python 3's asyncio interface.

:copyright: (c) 2015 Functional Software, Inc
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import, unicode_literals

import os.path

from setuptools import setup


# Hack to prevent stupid "TypeError: 'NoneType' object is not callable" error
# in multiprocessing/util.py _exit_function when running `python
# setup.py test` (see
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html)
for m in ('multiprocessing', 'billiard'):
    try:
        __import__(m)
    except ImportError:
        pass

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

tests_require = [
    'flake8>=2.1.0,<2.2.0',
    'pytest>=2.5.0,<2.6.0',
    'pytest-cov>=1.6,<1.7',
]


install_requires = [
    'aiohttp>=0.19',
    'raven>=5.4.0',
]

setup(
    name='raven-aiohttp',
    version='0.3.0',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='https://github.com/getsentry/raven-aiohttp',
    description='An asyncio transport for raven-python',
    long_description=open('README.md').read(),
    py_modules=['raven_aiohttp'],
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'test': tests_require,
    },
    license='BSD',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development'
    ],
)
