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
        self._len = os.fstat(self._fd).st_size // self._rsize

    def __len__(self):
        return self._len

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

class DjVuCorpus(Corpus):

    has_interps = False

    def __init__(self, id, title, path, public=True):
        Corpus.__init__(self, id, title, path, public)
        self._coordinates_map = Map('%s.djvu.coordinates' % path, '< HHHH')
        self._pagesize_map = Map('%s.djvu.pagesizes' % path, '< I HH')
        with open('%s.djvu.filenames' % path, 'rt') as file:
            self._filenames = map(str.rstrip, file.readlines())
        self._document_range_map = Map('%s.poliqarp.chunk.image' % path, '< IIII')

    def get_coordinates(self, id):
        return self._coordinates_map[id]

    def get_document_info(self, id):
        for n, (l, r, _, _) in enumerate(self._document_range_map):
            if l <= id <= r:
                return l, self._filenames[n]

    def get_page_info(self, id):
        l = 0
        r = len(self._pagesize_map)
        while l < r:
            mid = (l + r) // 2
            if id < self._pagesize_map[mid][0]:
                r = mid
            else:
                l = mid + 1
        i = l - 1
        base_id, width, height = self._pagesize_map[i]
        return i, width, height

    def get_url(self, id):
        x0, y0, x1, y1 = self.get_coordinates(id)
        w = x1 - x0
        h = y1 - y0
        baseid, filename = self.get_document_info(id)
        page0, _, _ = self.get_page_info(baseid)
        page, pw, ph = self.get_page_info(id)
        page -= page0
        cx = (x0 + x1) / (2.0 * pw)
        cy = 1 - (y0 + y1) / (2.0 * ph)
        return '%s?djvuopts&page=%d&highlight=%d,%d,%d,%d&zoom=width&showposition=%.3f,%.3f' % (filename, page + 1, x0, y0, w, h, cx, cy)

    def enhance_results(self, results):
        from utils.redirect import protect_url
        for result in results:
            for (column, segments) in result:
                for segment in segments:
                    segment.interps = None
                    if segment.id is None:
                        continue
                    url = self.get_url(segment.id)
                    segment.href = protect_url(url)

    def enhance_metadata(self, metadata):
        return ()

# vim:ts=4 sw=4 et
