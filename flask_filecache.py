import os
import shutil
import time
import errno
import tempfile

from flask import current_app

DEFAULT_CONFIG = {
    'FILECACHE_DIR': '/tmp/flask-filecache.cache_dir',
    'FILECACHE_THRESHOLD': 500,
    'FILECACHE_TIMEOUT': 3000,
    'FILECACHE_MODE': 0o600
}


class FileCache(object):
    """
    Note that cache directory must not be used for anything else.
    """

    _fs_transaction_suffix = '__cache_tmp'

    def __init__(self, app=None, cache_dir=None, threshold=None, timeout=None, mode=None):
        if cache_dir: self._path = cache_dir
        if threshold: self._threshold = threshold
        if timeout: self._timeout = timeout
        if mode: self._mode = mode

        self.app = app

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        for k, v in DEFAULT_CONFIG.items():
            app.config.setdefault(k, v)

        self._path = getattr(self, '_path', app.config['FILECACHE_DIR'])
        self._threshold = getattr(self, '_threshold', app.config['FILECACHE_THRESHOLD'])
        self._timeout = getattr(self, '_timeout', app.config['FILECACHE_TIMEOUT'])
        self._mode = getattr(self, '_mode', app.config['FILECACHE_MODE'])

        try:
            os.makedirs(self._path)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise

    def _list_dir(self):
        """
        Return a list of (fully qualified) cache filenames.
        """
        return [os.path.join(self._path, fn) for fn in os.listdir(self._path)]

    def _prune(self):
        entries = self._list_dir()
        if len(entries) > self._threshold:
            now = time.time()
            try:
                for idx, fname in enumerate(entries):
                    remove = False
                    mtime = os.path.getmtime(fname)
                    remove = (mtime < now) or idx % 3 == 0

                    if remove:
                        os.remove(fname)
            except (IOError, OSError):
                pass

    def clear(self):
        """
        Clear cache contents. 
        Returns True on success, False if failed.
        """
        for fname in self._list_dir():
            try:
                os.remove(fname)
            except (IOError, OSError):
                return False
        return True

    def get(self, filename):
        """
        Get path to cached file identified by filename.
        Returns None if failed.
        """
        try:
            path = os.path.join(self._path, filename)
            mtime = os.path.getmtime(path)
            if mtime >= time.time():
                return path
            else:
                os.remove(path)
                return None
        except (IOError, OSError):
            return None

    def put(self, filename, data, timeout=None):
        """
        Write data to cache and make it accesible using the filename provided.
        Returns path to cached file or None if failed.
        """
        if timeout is None:
            expires = int(time.time() + self._timeout)
        elif timeout != 0:
            expires = int(time.time() + timeout)
        self._prune()
        path = os.path.join(self._path, filename)
        try:
            fd, tmp = tempfile.mkstemp(suffix=self._fs_transaction_suffix,
                                       dir=self._path)
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
            os.rename(tmp, path)
            os.utime(path, (expires, expires))
            os.chmod(path, self._mode)
        except (IOError, OSError):
            return None
        else:
            return path

    def put_file(self, path, timeout=None):
        """
        Copy file to cache from the path supplied.
        Returns path to cached file or None if failed.
        """
        if timeout is None:
            expires = int(time.time() + self._timeout)
        elif timeout != 0:
            expires = int(time.time() + timeout)
        self._prune()
        try:
            cached = shutil.copy(path, self._path)
            os.utime(cached, (expires, expires))
            os.chmod(cached, self._mode)
        except (IOError, OSError):
            return None
        else:
            return cached

    def delete(self, filename):
        """
        Delete file from cache.
        Returns True on success, False otherwise.
        """
        try:
            os.remove(os.path.join(self._path, filename))
        except (IOError, OSError):
            return False
        else:
            return True

    def has(self, filename):
        """
        Check if the file with such name exists in the cache.
        """
        try:
            path = os.path.join(self._path, filename)
            mtime = os.path.getmtime(path)
            if mtime >= time.time():
                return True
            else:
                os.remove(path)
                return False
        except (IOError, OSError):
            return False


def test():
    from flask import Flask

    app = Flask(__name__)
    cache = FileCache(app)

    assert(cache.clear())

    data = b'Test data'
    filename = 'test.dat'

    path = cache.put(filename, data)

    assert(os.path.isfile(path))
    assert(cache.has(filename))
    assert(os.path.isfile(cache.get(filename)))

    with open(cache.get(filename), 'rb') as f:
        assert(f.read() == data)

    another = 'test_fleeting.dat'
    path = cache.put(another, data, timeout=3)
    print('Waiting 5 seconds')
    time.sleep(5)

    assert(cache.has(filename))
    assert(not cache.has(another))

    path = cache.put(another, data)

    assert(cache.delete(filename))
    assert(not cache.has(filename))

    assert(cache.clear())
    assert(not cache.has(another))

    assert(not cache.delete('bad name'))
    assert(not cache.get('bad name'))
    assert(not cache.has('bad name'))

    temp = os.path.join('/tmp', filename)
    with open(temp, 'wb') as f:
        f.write(data)

    path = cache.put_file(temp)
    path = cache.put_file(temp)

    assert(os.path.isfile(path))
    assert(cache.has(filename))

    assert(cache.clear())


if __name__ == '__main__':
    test()