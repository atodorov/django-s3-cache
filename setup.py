#!/usr/bin/env python

import os
import sys
from setuptools import setup, find_packages


def execute_tests():
    """
    Standalone django model test with a 'memory-only-django-installation'.
    You can play with a django model without a complete django app installation.
    http://www.djangosnippets.org/snippets/1044/
    """
    import django

    sys.exc_clear()

    os.environ["DJANGO_SETTINGS_MODULE"] = "django.conf.global_settings"
    from django.conf import global_settings

    global_settings.INSTALLED_APPS = ()
    global_settings.MIDDLEWARE_CLASSES = ()
    global_settings.SECRET_KEY = "not-very-secret"

    global_settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        }

    # http://django.readthedocs.org/en/latest/releases/1.7.html#standalone-scripts
    if django.VERSION >= (1,7):
        django.setup()

    from django.test.utils import get_runner
    test_runner = get_runner(global_settings)

    test_runner = test_runner()
    failures = test_runner.run_tests(['s3cache'])
    sys.exit(failures)


with open('README.rst') as file:
    long_description = file.read()

config = {
    'name' : 'django-s3-cache',
    'version' : '1.4.1',
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
    'test_suite' : '__main__.execute_tests',
}

if (len(sys.argv) >= 2) and (sys.argv[1] == '--requires'):
    for req in config['install_requires']:
        print req
else:
    setup(**config)
