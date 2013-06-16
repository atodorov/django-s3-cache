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

from storages.backends import s3boto
from django.core.files.base import ContentFile
from django.core.cache.backends.base import BaseCache

class AmazonS3Cache(BaseCache):
    def __init__(self, location, params):
        """
            location is not used but otherwise Django crashes.
        """

        BaseCache.__init__(self, params)

        # Amazon and boto has a maximum limit of 1000 for get_all_keys(). See:
        # http://docs.aws.amazon.com/AmazonS3/latest/API/RESTBucketGET.html
        # This implementation of the GET operation returns some or all (up to 1000) of the objects in a bucket....

        if self._max_entries > 1000:
            self._max_entries = 1000

        self._options = params.get('OPTIONS', {})

        # backward compatible syntax for s3cache users before v1.2 for easy upgrades
        # in v1.2 we update to latest django-storages 1.1.8 which changes variable names
        # in non-backward compatible fashion
        self._options['ACCESS_KEY'] = self._options.get('ACCESS_KEY_ID', None)
        self._options['SECRET_KEY'] = self._options.get('SECRET_ACCESS_KEY', None)
        self._options['BUCKET_NAME'] = self._options.get('STORAGE_BUCKET_NAME', None)

        # we use S3 compatible varibale names while django-storages doesn't
        _BUCKET_NAME = self._options.get('BUCKET_NAME', None)
        _DEFAULT_ACL = self._options.get('DEFAULT_ACL', 'private')
        _BUCKET_ACL  = self._options.get('BUCKET_ACL', _DEFAULT_ACL)
        # in case it was not specified in OPTIONS default to 'private'
        self._options['BUCKET_ACL'] = _BUCKET_ACL

        # sanitize location by removing leading and traling slashes
        self._LOCATION = self._options.get('LOCATION', self._options.get('location', ''))

        while self._LOCATION.startswith('/'):
            self._LOCATION = self._LOCATION[1:]

        while self._LOCATION.endswith('/'):
            self._LOCATION = self._LOCATION[:-1]

        # overwrite value specified by user
        self._options['LOCATION'] = self._LOCATION

        # S3BotoStorage wants lower case names
        for name, value in self._options.items():
            if value is not None: # skip None values
                self._options[name.lower()] = value

        self._storage = s3boto.S3BotoStorage(
                                    acl=_DEFAULT_ACL,
                                    bucket=_BUCKET_NAME,
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
            now = time.time()
            content = pickle.dumps(now + timeout, pickle.HIGHEST_PROTOCOL)
            content += pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
            self._storage.save(fname, ContentFile(content))
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

        if not self._max_entries:
            return
        elif int(self._num_entries) < self._max_entries:
            return

        try:
            keylist = self._storage.bucket.get_all_keys(prefix=self._LOCATION)
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

            UPDATE: this is wrong, md5() is still faster, see:
            http://atodorov.org/blog/2013/02/05/performance-test-md5-sha1-sha256-sha512/
        """
        return hashlib.sha1(key).hexdigest()

    def _get_num_entries(self):
        """
            There seems to be an artificial limit of 1000
        """
        return len(self._storage.bucket.get_all_keys(prefix=self._LOCATION))
    _num_entries = property(_get_num_entries)

    def clear(self):
        try:
            all_keys = self._storage.bucket.get_all_keys(prefix=self._LOCATION)
            self._storage.bucket.delete_keys(all_keys, quiet=True)
        except:
            pass

# For backwards compatibility
class CacheClass(AmazonS3Cache):
    pass
