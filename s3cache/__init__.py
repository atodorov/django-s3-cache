"Amazon S3 cache backend for Django"

# Copyright (c) 2012, Alexander Todorov <atodorov@nospam.otb.bg>
#
# Taken directly from django.core.cache.backends.filebased.FileBasedCache
# and adapted for S3.

import time
import hashlib

try:
    import cPickle as pickle
except ImportError:
    import pickle

import storages.backends.s3boto
from django.core.files.base import ContentFile
from django.core.cache.backends.base import BaseCache

class AmazonS3Cache(BaseCache):
    def __init__(self, params):
        BaseCache.__init__(self, params)

        # looks like Amazon or boto has a maximum limit of 1000 for
        # get_all_keys() which is not documented, so we play it safe here.
        if self._max_entries > 1000:
            self._max_entries = 1000

        self._options = params.get('OPTIONS', {})

        _ACCESS_KEY_NAME     = self._options.get('MAX_ENTRIES', s3boto.ACCESS_KEY_NAME)
        _SECRET_KEY_NAME     = self._options.get('AWS_SECRET_ACCESS_KEY', s3boto.AWS_SECRET_ACCESS_KEY)
        _HEADERS             = self._options.get('AWS_HEADERS', s3boto.AWS_HEADERS)
        _STORAGE_BUCKET_NAME = self._options.get('AWS_STORAGE_BUCKET_NAME', s3boto.AWS_STORAGE_BUCKET_NAME)
        _AUTO_CREATE_BUCKET  = self._options.get('AWS_AUTO_CREATE_BUCKET', s3boto.AWS_AUTO_CREATE_BUCKET)
#todo: make objects private, not public by default
#todo: add path prefix if not configured
        _DEFAULT_ACL         = self._options.get('AWS_DEFAULT_ACL', s3boto.AWS_DEFAULT_ACL)
        _BUCKET_ACL          = self._options.get('AWS_BUCKET_ACL', s3boto.AWS_BUCKET_ACL)
        _QUERYSTRING_AUTH    = self._options.get('AWS_QUERYSTRING_AUTH', s3boto.AWS_QUERYSTRING_AUTH)
        _QUERYSTRING_EXPIRE  = self._options.get('AWS_QUERYSTRING_EXPIRE', s3boto.AWS_QUERYSTRING_EXPIRE)
        _REDUCED_REDUNDANCY  = self._options.get('AWS_REDUCED_REDUNDANCY', s3boto.AWS_REDUCED_REDUNDANCY)
        _LOCATION            = self._options.get('AWS_LOCATION', s3boto.AWS_LOCATION)
        _CUSTOM_DOMAIN       = self._options.get('AWS_S3_CUSTOM_DOMAIN', s3boto.AWS_S3_CUSTOM_DOMAIN)
        _CALLING_FORMAT      = self._options.get('AWS_S3_CALLING_FORMAT', s3boto.AWS_S3_CALLING_FORMAT)
        _SECURE_URLS         = self._options.get('AWS_S3_SECURE_URLS', s3boto.AWS_S3_SECURE_URLS)
        _FILE_NAME_CHARSET   = self._options.get('AWS_S3_FILE_NAME_CHARSET', s3boto.AWS_S3_FILE_NAME_CHARSET)
        _FILE_OVERWRITE      = self._options.get('AWS_S3_FILE_OVERWRITE', s3boto.AWS_S3_FILE_OVERWRITE)
        _IS_GZIPPED          = self._options.get('AWS_IS_GZIPPED', s3boto.AWS_IS_GZIPPED)
        _PRELOAD_METADATA    = self._options.get('AWS_PRELOAD_METADATA', s3boto.AWS_PRELOAD_METADATA)
        _GZIP_CONTENT_TYPES  = self._options.get('GZIP_CONTENT_TYPES', s3boto.GZIP_CONTENT_TYPES)


        self._storage = s3boto.S3BotoStorage()   # todo
#todo: initialize S3 bucket and proper access credentials

    def add(self, key, value, timeout=None, version=None):
        if self.has_key(key, version=version):
            return False

        self.set(key, value, timeout, version=version)
        return True

    def get(self, key, default=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)

        fname = self._key_to_file(key)
        try:
            f = self._storage.open(fname, 'rb')
            try:
                exp = pickle.load(f)
                now = time.time()
                if exp < now:
                    self._delete(fname)
                else:
                    return pickle.load(f)
            finally:
                f.close()
        except (IOError, OSError, EOFError, pickle.PickleError):
            pass
        return default

    def set(self, key, value, timeout=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)

        fname = self._key_to_file(key)

        if timeout is None:
            timeout = self.default_timeout

        self._cull()

        try:
            f = self._storage.open(fname, 'wb')
            try:
                now = time.time()
                pickle.dump(now + timeout, f, pickle.HIGHEST_PROTOCOL)
                pickle.dump(value, f, pickle.HIGHEST_PROTOCOL)
            finally:
                f.close()
        except (IOError, OSError, EOFError, pickle.PickleError):
            pass

    def delete(self, key, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        try:
            self._delete(self._key_to_file(key))
        except (IOError, OSError):
            pass

    def _delete(self, fname):
        self._storage.delete(fname)

    def has_key(self, key, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        fname = self._key_to_file(key)
        try:
            f = self._storage.open(fname, 'rb')
            try:
                exp = pickle.load(f)
                now = time.time()
                if exp < now:
                    self._delete(fname)
                    return False
                else:
                    return True
            finally:
                f.close()
        except (IOError, OSError, EOFError, pickle.PickleError):
            return False

    def _cull(self):
        if int(self._num_entries) < self._max_entries:
            return

        try:
            keylist = self._storage.bucket.get_all_keys()
        except:
            return

        if self._cull_frequency == 0:
            doomed = keylist
        else:
            doomed = [k for (i, k) in enumerate(keylist) if i % self._cull_frequency == 0]

        try:
            self._storage.bucket.delete_keys(doomed, quiet=True)
        except:
            pass

    def _key_to_file(self, key):
        """
            All files go into a single flat directory because it's not easier
            to search/delete empty directories in _delete().

            Plus Amazon S3 doesn't seem to have a problem with many files into one directory.

            NB: measuring sha1() with timeit shows it is a bit faster compared to md5()
            http://stackoverflow.com/questions/2241013/is-there-a-significant-overhead-by-using-different-versions-of-sha-hashing-hash
        """
        return hashlib.sha1(key).hexdigest()

    def _get_num_entries(self):
        """
            There seems to be an artificial limit of 1000
        """
        return len(self._storage.bucket.get_all_keys())
    _num_entries = property(_get_num_entries)

    def clear(self):
        try:
            all_keys = self._storage.bucket.get_all_keys()
            self._storage.bucket.delete_keys(all_keys, quiet=True)
        except:
            pass

# For backwards compatibility
class CacheClass(AmazonS3Cache):
    pass
