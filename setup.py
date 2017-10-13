"""
raven-aiohttp
=============

A transport for `raven-python <https://github.com/getsentry/raven-python>`_
which supports Python 3's asyncio interface.

:copyright: (c) 2015 Functional Software, Inc
:license: BSD, see LICENSE for more details.
"""
import io
import os
import re
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


def get_version():
    regex = r"__version__\s=\s\'(?P<version>.+?)\'"

    return re.search(regex, read('raven_aiohttp.py')).group('version')


def read(*parts):
    filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), *parts)

    with io.open(filename, encoding='utf-8', mode='rt') as fp:
        return fp.read()


tests_require = [
    'flake8',
    'isort',
    'pytest',
    'pytest-asyncio<0.6.0',  # to support Python 3.5-
    'pytest-cov',
    'pytest-mock'
]


install_requires = [
    'aiohttp>=2.0',
    'raven>=5.4.0',
]


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='raven-aiohttp',
    version=get_version(),
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='https://github.com/getsentry/raven-aiohttp',
    description='An asyncio transport for raven-python',
    long_description=read('README.rst'),
    py_modules=['raven_aiohttp'],
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'test': tests_require,
    },
    cmdclass={
        'test': PyTest,
    },
    license='BSD',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development',
    ],
)
