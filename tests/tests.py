# pylint: disable=missing-docstring,protected-access

from s3cache import AmazonS3Cache
from django.test import TestCase

class S3CacheTestCase(TestCase):
    pass

class CacheConfigurationTest(S3CacheTestCase):
    def test_old_style_options(self):
        """
            Test django-storages < 1.1.8 options syntax, which
            needs to be translated to latest syntax
        """
        cache = AmazonS3Cache(
            None, # location
            {
                'BACKEND': 's3cache.AmazonS3Cache',
                'OPTIONS' : {
                    'ACCESS_KEY_ID' : 'access_key_old',
                    'SECRET_ACCESS_KEY' : 'secret_key_old',
                    'STORAGE_BUCKET_NAME': 'bucket_old',
                }
            }
        )

        self.assertEqual(cache._options['access_key'], 'access_key_old')
        self.assertEqual(cache._options['secret_key'], 'secret_key_old')
        self.assertEqual(cache._options['bucket_name'], 'bucket_old')

    def test_new_style_options(self):
        """
            Test django-storages >= 1.1.8 options syntax
        """
        cache = AmazonS3Cache(
            None, # location
            {
                'BACKEND': 's3cache.AmazonS3Cache',
                'OPTIONS' : {
                    'ACCESS_KEY' : 'access_key_new',
                    'SECRET_KEY' : 'secret_key_new',
                    'BUCKET_NAME': 'bucket_new',
                }
            }
        )

        self.assertEqual(cache._options['access_key'], 'access_key_new')
        self.assertEqual(cache._options['secret_key'], 'secret_key_new')
        self.assertEqual(cache._options['bucket_name'], 'bucket_new')

    def test_mixed_style_options(self):
        """
            Test MIXED options syntax (upgrade leftovers)
        """
        cache = AmazonS3Cache(
            None, # location
            {
                'BACKEND': 's3cache.AmazonS3Cache',
                'OPTIONS' : {
                    'ACCESS_KEY_ID' : 'access_key_mix', # old
                    'SECRET_KEY' : 'secret_key_mix',
                    'STORAGE_BUCKET_NAME': 'bucket_mix', # old
                }
            }
        )

        self.assertEqual(cache._options['access_key'], 'access_key_mix')
        self.assertEqual(cache._options['secret_key'], 'secret_key_mix')
        self.assertEqual(cache._options['bucket_name'], 'bucket_mix')

    # pylint: disable=invalid-name
    def test_lowercase_new_style_options(self):
        """
            Test django-storages >= 1.1.8 options syntax in lower case.
            django-s3-cache v1.3 README was showing lowercase names for the options
            but those were overriden by the backward compatibility code and
            set to None. The issue comes from s3cache automatically converting
            everything to lower case before passing it down to django-storages
            which uses only lower case names for its class attributes.

            Documentation was updated in 3aaa0f254a2e0e389961b2112a00d3edf3e1ee90

            Real usage of lower case option names:
            https://github.com/atodorov/django-s3-cache/issues/2#issuecomment-65423398
        """
        cache = AmazonS3Cache(
            None, # location
            {
                'BACKEND': 's3cache.AmazonS3Cache',
                'OPTIONS' : {
                    'access_key' : 'access_key_low',
                    'secret_key' : 'secret_key_low',
                    'bucket_name': 'bucket_low',
                }
            }
        )

        self.assertEqual(cache._options['access_key'], 'access_key_low')
        self.assertEqual(cache._options['secret_key'], 'secret_key_low')
        self.assertEqual(cache._options['bucket_name'], 'bucket_low')
