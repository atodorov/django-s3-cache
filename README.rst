Django S3 Cache
---------------

.. image:: https://travis-ci.org/atodorov/django-s3-cache.svg?branch=master
   :target: https://travis-ci.org/atodorov/django-s3-cache
   :alt: Build status

.. image:: https://coveralls.io/repos/github/atodorov/django-s3-cache/badge.svg?branch=master
   :target: https://coveralls.io/github/atodorov/django-s3-cache?branch=master
   :alt: Code coverage

.. image:: https://api.codeclimate.com/v1/badges/634faffb0ab0a5c81355/maintainability
   :target: https://codeclimate.com/github/atodorov/django-s3-cache/maintainability
   :alt: Maintainability


This is Amazon Simple Storage Service (S3) cache backend for Django.
It is based on the *django.core.cache.backends.filebased.FileBasedCache* backend
and operates in similar fashion. This backend uses
`django-storages <http://pypi.python.org/pypi/django-storages>`_ to read/write the
data into S3. It uses the *s3boto* storage backend.

All key/values passed to this backend are stored in a flat directory structure
in your S3 bucket. It uses sha1 instead of md5 to create the file name.


**This project is looking for maintainers!**


Installation
============

Use pip to install from PyPI:

::

        pip install django-s3-cache


Configure the use of this backend:

::

        CACHES = {
            'default': {
                'BACKEND': 's3cache.AmazonS3Cache',
                'OPTIONS': {
                    'ACCESS_KEY' : 'Your AWS access key',
                    'SECRET_KEY' : 'Your AWS secret access key',
                    'BUCKET_NAME': 'Your AWS storage bucket name',
                    'LOCATION'   : 'directory_prefix',
                }
            }
        }

Changelog
=========

* 1.4.3 (10 Nov 2019)

  * switch license from BSD-3-Clause to MIT
  * Switched to Travis-CI
  * Started testing with pylint
  * Internal code refactoring and more testing

Configuration
=============

Django S3 Cache supports many configuration options. They should be defined as
keys of the *OPTIONS* dictionary in *settings.py* as shown above. If something
is not defined explicitly it follows the defaults of *s3boto* backend from
*django-storages* which in turn reads them from *settings.py*.

**NOTE-1:** some values in *settings.py* may be used globally by *boto* and other AWS aware
Django components since they follow the format *AWS_XXXX*. It's always best to define your
values as cache options explicitly if you don't want to run into problems.

**NOTE-2:** since version 1.2 Django S3 Cache is compatible with django-storages v1.1.8 which
has changed the names of configuration variables. All new variables are expected to be lower
case and the AWS keys variables changed names. For exact names see the S3BotoStorage class
definition in *s3boto.py*. Django S3 Cache implements backward compatibility with its previous
OPTIONS syntax to allow for easier upgrades. Older names are mapped to new ones and all
options are lower cased before passing to S3BotoStorage. The example above shows the new syntax.

**NOTE-3:** before version 1.3 there is a **CRITICAL BUG** in the handling of the *LOCATION*
option. If used cache objects will be stored under the defined directory, however culling
and clearing the cache **was not** taking this into account. cache.clear() or cache._cull()
will **delete the entire bucket**. This has been fixed in version 1.3!

**NOTE-4:** in versions 1.2 to 1.3 there is a **BUG** in the backward compatibility handling
of *OPTIONS*. If you have been using the new style syntax for *ACCESS_KEY*, *SECRET_KEY*,
*BUCKET_NAME* it would be overriden and boto will crash due to missing authentication parameters.
This has been fixed in version 1.4!

Some notable options are:

* *LOCATION* - the directory prefix under which to store cache files. Defaults to empty string, which means the root directory;
* *DEFAULT_ACL* == *private* - default ACL for created objects. Unlike the *s3boto* storage backend we set this to *private*;
* *BUCKET_ACL* == *DEFAULT_ACL* - ACL for the bucket if auto created. By default set to *private*. It's best to use separate bucket for cache files;
* *REDUCED_REDUNDANCY* - set to *True* if you want to save a few cents on storage costs;
* *IS_GZIPPED* - set to *True* to enable Gzip compression. Used together with *GZIP_CONTENT_TYPES*. See *django-storages* `documentation <http://django-storages.readthedocs.org/en/latest/backends/amazon-S3.html>`_.


Django S3 implements culling strategy similar to the stock filesystem backend. It will honor the following options:

* *MAX_ENTRIES* - the maximum number of entries allowed in the cache before old values are deleted. If 0 culling is disabled. This argument defaults to 300;
* *CULL_FREQUENCY* - the fraction of entries that are culled when *MAX_ENTRIES* is reached. The actual ratio is *1/CULL_FREQUENCY*, so set *CULL_FREQUENCY* to 2 to cull half of the entries when *MAX_ENTRIES* is reached;


Contributing
============

Source code and issue tracker are at https://github.com/atodorov/django-s3-cache
