import base64
import hashlib
import urllib

import django.http
from django.views.generic.simple import redirect_to as simple_redirect
from django.conf import settings

def protect_url(url):
    key = hash_url(url)
    quoted_url = urllib.quote(url, safe='/:')
    if quoted_url.startswith('http://'):
        tail = quoted_url[7:]
    else:
        raise ValueError('''URL to protect doesn't start with 'http://': %r''' % quoted_url)
    return django.core.urlresolvers.reverse(safe_redirect, kwargs=dict(key=key, scheme='http', tail=tail))

def hash_url(url):
    digest = hashlib.md5(settings.SECRET_KEY + url).digest()
    return base64.urlsafe_b64encode(digest)[:5]

def safe_redirect(self, key, scheme, tail):
    url = '%s://%s' % (scheme, tail)
    if key != hash_url(url):
        raise django.http.Http404
    return django.http.HttpResponseRedirect(url)

# vim:ts=4 sw=4 et
