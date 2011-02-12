import django.conf
import django.http

from .views import get_corpus_by_id

def view(request, corpus_id, n_from, n_to):
    n_from = int(n_from, 10)
    n_to = int(n_to, 10)
    if 0 <= n_from <= n_to:
        if n_to - n_from > django.conf.settings.MAX_MATCH_LENGTH:
            raise django.http.Http404
    else:
        raise django.http.Http404
    corpus = get_corpus_by_id(corpus_id)
    result = [None]
    for i in xrange(n_from, n_to + 1):
        try:
            baseid, _, filename = corpus.get_document_info(i)
            page0, _, _ = corpus.get_page_info(baseid)
            page, _, _ = corpus.get_page_info(i)
            page -= page0
            x0, y0, x1, y1 = corpus.get_coordinates(i)
        except LookupError:
            raise django.http.Http404
        result += ['%d %d %d %d %d' % (page, x0, y0, x1, y1)]
    result[0] = filename
    result += ['']
    result = '\n'.join(result)
    response = django.http.HttpResponse(result)
    response['Content-Type'] = 'text/plain'
    return response

# vim:ts=4 sw=4 et
