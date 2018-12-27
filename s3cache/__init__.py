"Amazon S3 cache backend for Django"

# Copyright (c) 2012,2017 Alexander Todorov <atodorov@MrSenko.com>
#
# Taken directly from django.core.cache.backends.filebased.FileBasedCache
# and adapted for S3.

import time
import hashlib

try:
    import cPickle as pickle
except ImportError:
    import pickle

from storages.backends import s3boto
from django.core.files.base import ContentFile
from django.core.cache.backends.base import BaseCache

def _key_to_file(key):
    """
        All files go into a single flat directory because it's not easier
        to search/delete empty directories in _delete().

        Plus Amazon S3 doesn't seem to have a problem with many files into one directory.

        NB: measuring sha1() with timeit shows it is a bit faster compared to md5()
        http://stackoverflow.com/questions/2241013/is-there-a-significant-overhead-by-using-different-versions-of-sha-hashing-hash

        UPDATE: this is wrong, md5() is still faster, see:
        http://atodorov.org/blog/2013/02/05/performance-test-md5-sha1-sha256-sha512/
    """
    return hashlib.sha1(key.encode('utf-8')).hexdigest()

class AmazonS3Cache(BaseCache):
    """
        Amazon S3 cache backend for Django
    """
    def __init__(self, _location, params):
        """
            location is not used but otherwise Django crashes.
        """

        BaseCache.__init__(self, params)

        # Amazon and boto have a maximum limit of 1000 for get_all_keys(). See:
        # http://docs.aws.amazon.com/AmazonS3/latest/API/RESTBucketGET.html
        # This implementation of the GET operation returns some or all (up to 1000)
        # of the objects in a bucket....

        if self._max_entries > 1000:
            self._max_entries = 1000

        self._options = params.get('OPTIONS', {})

        # backward compatible syntax for s3cache users before v1.2 for easy upgrades
        # in v1.2 we update to latest django-storages 1.1.8 which changes variable names
        # in non-backward compatible fashion
        if 'ACCESS_KEY' not in self._options.keys():
            self._options['ACCESS_KEY'] = self._options.get('ACCESS_KEY_ID', None)
        if 'SECRET_KEY' not in self._options.keys():
            self._options['SECRET_KEY'] = self._options.get('SECRET_ACCESS_KEY', None)
        if 'BUCKET_NAME' not in self._options.keys():
            self._options['BUCKET_NAME'] = self._options.get('STORAGE_BUCKET_NAME', None)

        # we use S3 compatible varibale names while django-storages doesn't
        _bucket_name = self._options.get('BUCKET_NAME', None)
        _default_acl = self._options.get('DEFAULT_ACL', 'private')
        _bucket_acl = self._options.get('BUCKET_ACL', _default_acl)
        # in case it was not specified in OPTIONS default to 'private'
        self._options['BUCKET_ACL'] = _bucket_acl


        self._location = self._options.get('LOCATION', self._options.get('location', ''))
        # sanitize location by removing leading and traling slashes
        self._options['LOCATION'] = self._location.strip('/')

        # S3BotoStorage wants lower case names
        lowercase_options = []
        for name, value in self._options.items():
            if value: # skip None values
                lowercase_options.append((name.lower(), value))
        # this avoids RuntimeError: dictionary changed size during iteration
        # with Python 3 if we assign to the dictionary directly
        for _n, _v in lowercase_options:
            self._options[_n] = _v

        self._storage = s3boto.S3BotoStorage(
            acl=_default_acl,
            bucket=_bucket_name,
            **self._options
        )


    def add(self, key, value, timeout=None, version=None):
        if self.has_key(key, version=version):
            return False

        self.set(key, value, timeout, version=version)
        return True

    def get(self, key, default=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)

        fname = _key_to_file(key)
        try:
            fobj = self._storage.open(fname, 'rb')
            try:
                if not self._is_expired(fobj, fname):
                    return pickle.load(fobj)
            finally:
                fobj.close()
        except (IOError, OSError, EOFError, pickle.PickleError):
            pass
        return default

    def set(self, key, value, timeout=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)

        fname = _key_to_file(key)

        self._cull()

        try:
            content = self._dump_object(value, timeout)
            self._storage.save(fname, ContentFile(content))
        except (IOError, OSError, EOFError, pickle.PickleError):
            pass

    def _dump_object(self, value, timeout=None):
        if timeout is None:
            timeout = self.default_timeout

        content = pickle.dumps(time.time() + timeout, pickle.HIGHEST_PROTOCOL)
        content += pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
        return content

    def delete(self, key, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        try:
            self._delete(_key_to_file(key))
        except (IOError, OSError):
            pass

    def _delete(self, fname):
        self._storage.delete(fname)

    def has_key(self, key, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        fname = _key_to_file(key)
        try:
            fobj = self._storage.open(fname, 'rb')
            try:
                return not self._is_expired(fobj, fname)
            finally:
                fobj.close()
        except (IOError, OSError, EOFError, pickle.PickleError):
            return False

    def _is_expired(self, fobj, fname):
        """
            Takes an open cache file and determines if it has expired,
            deletes the file if it is has passed its expiry time.
        """
        exp = pickle.load(fobj)
        if exp < time.time():
            self._delete(fname)
            return True

        return False

    def _cull(self, frequency=None):
        if frequency is None:
            frequency = self._cull_frequency

        if not self._max_entries:
            return

        if int(self._num_entries) < self._max_entries:
            return

        try:
            keylist = self._storage.bucket.get_all_keys(prefix=self._location)
        except (IOError, OSError):
            return

        if not frequency:
            doomed = keylist
        else:
            doomed = [k for (i, k) in enumerate(keylist) if i % frequency == 0]

        try:
            self._storage.bucket.delete_keys(doomed, quiet=True)
        except (IOError, OSError):
            pass


    def _get_num_entries(self):
        """
            There seems to be an artificial limit of 1000
        """
        return len(self._storage.bucket.get_all_keys(prefix=self._location))
    _num_entries = property(_get_num_entries)

    def clear(self):
        # delete all keys
        self._cull(0)

# For backwards compatibility
class CacheClass(AmazonS3Cache):
    """
        Backward compatibility class definition
    """
