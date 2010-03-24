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

DEBUG = False

# vim:ts=4 sw=4 et
