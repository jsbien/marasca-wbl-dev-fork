# encoding=UTF-8

from __future__ import with_statement

import mmap
import os
import struct

import poliqarp

import django.utils.datastructures
from django.utils.translation import ugettext_lazy

class Map(object):

    def __init__(self, path, format):
        self._fd = os.open(path, os.O_RDONLY)
        self._map = mmap.mmap(self._fd, 0, mmap.MAP_SHARED, mmap.PROT_READ)
        self._format = format
        nargs = sum(1 for char in format if char.isalpha())
        self._rsize = len(struct.pack(format, *(nargs * [0])))

    def __getitem__(self, n):
        rsize = self._rsize
        chunk = ''.join(self._map[x] for x in xrange(n * rsize, (n + 1) * rsize))
        result = struct.unpack(self._format, chunk)
        if len(result) == 1:
            return result[0]
        else:
            return result
    
    def close(self):
        try:
            self._map.close()
        except AttributeError:
            pass
        else:
            del self._map
        try:
            os.close(self._fd)
        except AttributeError:
            pass
        else:
            del self._fd
    
    def __del__(self):
        self.close()

class Corpus(object):

    has_metadata = False
    has_interps = True

    def __init__(self, id, title, path=None, public=True):
        self.id = id
        self.title = title
        self.path = path
        self.public = public

    def enhance_results(self, results):
        return

    def enhance_metadata(self, metadata):
        return metadata

class OldIpiCorpus(Corpus):

    has_metadata = True

    # TODO: support multiple metadata values

    _i18n_style = {
        u'artystyczny': ugettext_lazy(u'artistic genre'),
        u'proza': ugettext_lazy(u'prose'),
        u'poezja': ugettext_lazy(u'poetry'),
        u'dramat': ugettext_lazy(u'drama'),
        u'publicystyczny': ugettext_lazy(u'news and commentaries'),
        u'literatura faktu': ugettext_lazy(u'non-fiction'),
        u'naukowo-dydaktyczny': ugettext_lazy(u'scientific and educational genre'),
        u'naukowy humanistyczny': ugettext_lazy(u'humanistic'),
        u'naukowy przyrodniczy': ugettext_lazy(u'nature'),
        u'naukowy techniczny': ugettext_lazy(u'technical'),
        u'popularno-naukowy': ugettext_lazy(u'popular science'),
        u'podręcznik': ugettext_lazy(u'textbook'),
        u'urzędowo-kancelaryjny': ugettext_lazy(u'official style'),
        u'protokół': ugettext_lazy(u'protocol'),
        u'ustawa': ugettext_lazy(u'law'),
        u'informacyjno-poradnikowy': ugettext_lazy(u'books and guides'),
        u'potoczny': ugettext_lazy(u'colloquial style'),
    }

    _i18n_medium = {
        u'prasa': ugettext_lazy(u'newspaper or periodical'),
        u'książka': ugettext_lazy(u'book'),
        u'internet': ugettext_lazy(u'internet'),
        u'rękopis': ugettext_lazy(u'manuscript'),
    }

    def i18n_style(self, value):
        return self._i18n_style.get(value, value)

    def i18n_medium(self, value):
        return self._i18n_medium.get(value, value)

    def enhance_metadata(self, tuples):
        metadata = django.utils.datastructures.MultiValueDict()
        date = future_date = poliqarp.Date(9999, 1, 1)
        for key, value in tuples:
            if isinstance(value, poliqarp.Date):
                date = min(date, value)
            else:
                metadata.appendlist(key, value)
        if date == future_date:
            date = None
        items = [
            (ugettext_lazy('author'), metadata.getlist('autor')),
            (ugettext_lazy('title'), metadata.getlist(u'tytuł')),
            (ugettext_lazy('date'), [date] if date is not None else []),
            (ugettext_lazy('publisher'), metadata.getlist('wydawca')),
            (ugettext_lazy('place of publication'), metadata.getlist('miejsce wydania')),
            (ugettext_lazy('style'), map(self.i18n_style, metadata.getlist('styl'))),
            (ugettext_lazy('medium'), map(self.i18n_medium, metadata.getlist('medium'))),
        ]
        result = django.utils.datastructures.SortedDict()
        for key, value in items:
            if value:
                result[key] = value
        return result

# vim:ts=4 sw=4 et
