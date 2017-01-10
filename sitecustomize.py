"""
    This file is used to configure Django for testing.
    It is placed in the user's site-packages directory and
    is loaded before each python process!
"""
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "django.conf.global_settings"

# pylint: disable=wrong-import-position
import django
from django.conf import global_settings

global_settings.INSTALLED_APPS = ('django_nose',)
global_settings.TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
global_settings.NOSE_ARGS = [
    '-x', '-v',
    '--with-coverage',
    '--cover-erase',
    '--cover-branches',
    '--cover-package=s3cache',
]
global_settings.MIDDLEWARE_CLASSES = ()
global_settings.SECRET_KEY = "not-very-secret"

global_settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}

# http://django.readthedocs.org/en/latest/releases/1.7.html#standalone-scripts
if django.VERSION >= (1, 7):
    django.setup()
