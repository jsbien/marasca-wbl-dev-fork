# encoding=UTF-8

# Copyright © 2009, 2010 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

def _get_corpora():

    import os.path
    from corpus import DjVuCorpus

    _corpora_dir = '/srv/poliqarp/corpora/'

    def _(x): return x

    return [
        DjVuCorpus(path=os.path.join(_corpora_dir, 'sw'),
            id='slownik-warszawski',
            title=_(u'J. Karłowicz, A. Kryński, W. Niedźwiedzki. Dictionary of Polish. Warsaw 1900–1927'),
            abbreviation='SW'
        ),
        DjVuCorpus(path=os.path.join(_corpora_dir, 'spxviw'),
            id='slownik-polszczyzny-xvi-wieku',
            title=_(u'S. Bąk, M. R. Mayenowa, F. Pepłowski (eds.). Dictionary of the 16th century Polish. Wrocław — Warszawa, 1966-???? (work in progress)'),
            abbreviation='SpXVIw'
        ),
        DjVuCorpus(path=os.path.join(_corpora_dir, 'linde'),
            id='slownik-lindego',
            title=_(u'M. Samuel Bogumił Linde. Dictionary of Polish (2nd edition). Lwów 1854-1861.'),
            abbreviation='Linde',
        ),
        DjVuCorpus(path=os.path.join(_corpora_dir, 'sgkp'),
            id='slownik-geograficzny',
            title=_(u'B. Chlebowski, F. Sulimierski, W. Walewski (ed.), The Geographical Dictionary of the Polish Kingdom and other Slavic Countries, Warszawa 1880-1902'),
            abbreviation='SGKP'
        ),
        DjVuCorpus(path=os.path.join(_corpora_dir, 'IMPACT_GT_1'),
            id='impact-gt-1',
            title=_(u'IMPACT GT corpus (1-d), 1570-1756'),
            abbreviation='IMPACT_GT_1',
            has_interps=True,
            public=False,
        ),
        DjVuCorpus(path=os.path.join(_corpora_dir, 'IMPACT_GT_2'),
            id='impact-gt-2',
            title=_(u'IMPACT GT corpus (2-d), 1570-1756'),
            abbreviation='IMPACT_GT_2',
            has_interps=True,
            public=False,
        ),
    ]

CORPORA = _get_corpora()
del _get_corpora

TEMPLATE_DIRS = (
    '/srv/poliqarp/marasca/templates/',
)
SESSION_LOCKS_DIRECTORY = '/srv/poliqarp/locks/'

SERVER_EMAIL = 'poliqarp@wbl.klf.uw.edu.pl'
ADMINS = MANAGERS = (
    ('WBL Administrator', 'wbladmin@poczta.klf.uw.edu.pl'),
)

SEND_BROKEN_LINK_EMAILS = True

QUERY_LOG = '/srv/poliqarp/marasca/logs/query-log'

BUFFER_SIZE = 10000

DEBUG = False

TIME_ZONE = 'Europe/Warsaw'

# vim:ts=4 sw=4 et
