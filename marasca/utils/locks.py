import fcntl
import os

from django.conf import settings

class SessionLock(object):

    def __init__(self, session, wait=0):
        self._filename = os.path.join(settings.SESSION_LOCKS_DIRECTORY, '%s.lock' % session.session_key)
        if wait > 0:
            # FIXME
            raise NotImplementedError

    def __enter__(self):
        self._fd = os.open(self._filename, os.O_CREAT | os.O_RDWR | os.O_TRUNC, 0666)
        fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def __exit__(self, ex_type, ex_value, ex_traceback):
        os.unlink(self._filename)
        os.close(self._fd)

# vim:ts=4 sw=4 et
