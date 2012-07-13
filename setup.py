#!/usr/bin/env python

from setuptools import setup, find_packages

with open('README.rst') as file:
    long_description = file.read()

setup(
    name = 'django-s3-cache',
    version = '1.0',
    packages = find_packages(),
    author = 'Alexander Todorov',
    author_email = 'atodorov@nospam.otb.bg',
    license = 'BSD',
    description = 'Amazon Simple Storage Service (S3) cache backend for Django',
    long_description = long_description,
    url='https://github.com/atodorov/django-s3-cache',
    keywords = ['Amazon', 'S3', 'Django', 'cache'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    zip_safe = False,
    install_requires=['boto','django-storages','Django']
)
