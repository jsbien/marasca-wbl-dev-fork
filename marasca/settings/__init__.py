TEMPLATE_DEBUG = DEBUG = False

ADMINS = MANAGERS = ()

LANGUAGE_CODE = 'en'

SITE_ID = 1

USE_I18N = True

ADMIN_MEDIA_PREFIX = '/admin-media/'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
)

if DEBUG:
    MIDDLEWARE_CLASSES += (
        'utils.profiling.ProfilingMiddleware',
    )

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    'templates/',
)

INSTALLED_APPS = (
    'django.contrib.sessions',
)

SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

def _(x): return x

LANGUAGES = (
    ('pl', _('Polish')),
    ('en', _('English')),
)

SESSION_LOCKS_DIRECTORY = '../locks/'
SESSION_LOCK_TIMEOUT = 5

BUFFER_SIZE = 1000
MAX_RANDOM_SAMPLE_SIZE = BUFFER_SIZE
MAX_RESULTS_PER_PAGE = 1000
QUERY_TIMEOUT = 0.5

# By default poliqarpd restricts life-time of an idle session to 1200 seconds.
# See max-session-idle setting in poliqarpd(1).
# This value should be *lower* than that one.
SESSION_REFRESH = 1000

SNIPPET_DEFAULT_SCREEN_DPI = 100 # wild guess
SNIPPET_MAX_WIDTH = 400
SNIPPET_MAX_HEIGHT = 200
SNIPPET_CACHE_SIZE = 128 << 20

try:
    from .secret_key import SECRET_KEY
except ImportError, ex:
    import sys
    print >>sys.stderr, 'Please run the setup script to create an initial configuration.'
    sys.exit(1)

def _get_hostname():
     import socket
     hostname = socket.gethostname()
     hostname = hostname.split('.')[0]
     return hostname
_hostname = _get_hostname()
_module = getattr(__import__('', locals(), globals(), [_hostname], 1), _hostname)
_data = dict((k, v) for k, v in vars(_module).items() if not k.startswith('_'))
vars().update(_data)
del _data, _module, _hostname, _get_hostname

# vim:ts=4 sw=4 et
