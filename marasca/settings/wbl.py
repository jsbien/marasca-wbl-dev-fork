# encoding=UTF-8

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
    ]

CORPORA = _get_corpora()
del _get_corpora

TEMPLATE_DIRS = (
    '/srv/poliqarp/marasca/templates/',
)
SESSION_LOCKS_DIRECTORY = '/srv/poliqarp/locks/'

ADMINS = MANAGERS = (
    ('Jakub Wilk', 'jwilk@localhost'),
)

SEND_BROKEN_LINK_EMAILS = True

QUERY_LOG = '/srv/poliqarp/marasca/logs/query-log'

DEBUG = False

TIME_ZONE = 'Europe/Warsaw'

# vim:ts=4 sw=4 et
