#!/usr/bin/env python

import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


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
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

with open('README.rst') as file:
    long_description = file.read()

config = {
    'name' : 'django-s3-cache',
    'version' : '1.4',
    'packages' : find_packages(),
    'author' : 'Alexander Todorov',
    'author_email' : 'atodorov@nospam.otb.bg',
    'license' : 'BSD',
    'description' : 'Amazon Simple Storage Service (S3) cache backend for Django',
    'long_description' : long_description,
    'url' : 'https://github.com/atodorov/django-s3-cache',
    'keywords' : ['Amazon', 'S3', 'Django', 'cache'],
    'classifiers' : [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    'zip_safe' : False,
    'install_requires' : ['boto','django-storages>=1.1.8','Django'],
    'cmdclass' : {'test': PyTest},
}

if (len(sys.argv) >= 2) and (sys.argv[1] == '--requires'):
    for req in config['install_requires']:
        print req
else:
    setup(**config)
