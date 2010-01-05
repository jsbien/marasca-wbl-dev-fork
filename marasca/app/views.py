from __future__ import with_statement

import contextlib
import sys
import time

import django.conf
import django.core.mail
import django.forms
import django.http
import django.template
import django.template.loader
import django.utils.translation

import utils.locks
import utils.i18n
import poliqarp

get_template = django.template.loader.get_template
ugettext_lazy = django.utils.translation.ugettext_lazy
global_settings = django.conf.settings

try:
    poliqarp.errors.InvalidSessionUserId
except AttributeError:
    # Fix typo in poliqarpd Python bindings:
    poliqarp.errors.InvalidSessionUserId = poliqarp.errors.InvalidSesssionUserId

class Context(django.template.RequestContext):

    def __init__(self, request, **kwargs):
        d = dict(kwargs)
        d.update(corpora = global_settings.CORPORA)
        django.template.RequestContext.__init__(self, request, d)

def process_index(request):
    template = get_template('index.html')
    context = Context(request, selected='index')
    return django.http.HttpResponse(template.render(context))

class QueryForm(django.forms.Form):
    query = django.forms.CharField(max_length=1000, label=ugettext_lazy('Query'))

def get_corpus_by_id(corpus_id):
    for corpus in django.conf.settings.CORPORA:
        if corpus.id == corpus_id:
            break
    else:
        raise django.http.Http404
    return corpus

def process_pending(request, corpus_id):
    template = get_template('pending.html')
    corpus = get_corpus_by_id(corpus_id)
    refresh_url = django.core.urlresolvers.reverse(process_query, kwargs=dict(corpus_id=corpus_id))
    context = Context(request, selected=corpus, refresh_url=refresh_url)
    response = django.http.HttpResponse(template.render(context))
    response['Refresh'] = '%d; %s' % (1, refresh_url)
    return response

class Info(object):

    def __repr__(self):
        return '<%s.%s with %s>' % (
            self.__module__, type(self).__name__,
            ', '.join('%s=%s' %
                (key, self._repr(key, value))
                for key, value in vars(self).iteritems()
                if not key.startswith('_')
            )
        )

    def _repr(self, key, value):
        return repr(value)

class PageInfo(Info):
    def __init__(self, corpus_id, page_start, n):
        self.n = n
        self.url = django.core.urlresolvers.reverse(process_query, kwargs=dict(corpus_id=corpus_id, page_start=page_start))

class QueryInfo(Info):

    def __init__(self):
        self.running = False
        self.l = None
        self.r = None
        self.n_stored_results = None
        self.n_spotted_results = None
        self.results = []
        self.selected = None

    def _repr(self, key, value):
        if key == 'results':
            return '[...]'
        else:
            return repr(value)

def redirect_to_pending(corpus_id):
    pending_url = django.core.urlresolvers.reverse(
        process_pending,
        kwargs=dict(corpus_id=corpus_id)
    )
    return django.http.HttpResponseRedirect(pending_url)

class ResultInfo(Info):

    def __init__(self, n):
        self.n = n
        self.context = ('', '', '', '')
        self.metadata = {}

def extract_result_info(connection, settings, corpus, n, extract_context=True, extract_metadata=True):
    if n >= connection.get_n_stored_results():
        raise django.http.Http404
    info = ResultInfo(n)
    if extract_context:
        info.context = connection.get_context(n) 
    if extract_metadata and corpus.has_metadata:
        info.metadata = connection.get_metadata(n, dict_type=corpus.enhance_metadata)
    return info

def run_query(connection, settings, corpus, query, l, r):
    connection.open_corpus(corpus.id)
    try:
        connection.make_query(query, force=settings.need_query_remake())
    except poliqarp.InvalidQuery, ex:
        return ex
    except poliqarp.Busy, ex:
        return redirect_to_pending(corpus.id)
    settings.need_query_remake(False)
    qinfo = QueryInfo()
    try:
        if settings.random_sample:
            connection.resize_buffer(settings.random_sample_size)
        else:
            connection.resize_buffer(global_settings.BUFFER_SIZE)
    except poliqarp.Busy:
        return redirect_to_pending(corpus.id)
    del settings.random_sample_size
    try:
        connection.run_query(
            global_settings.BUFFER_SIZE,
            timeout=global_settings.QUERY_TIMEOUT,
            force=settings.need_query_rerun()
        )
    except poliqarp.Busy:
        return redirect_to_pending(corpus.id)
    except poliqarp.QueryRunning:
        settings.need_query_rerun(False)
        qinfo.running = True
        if connection.get_n_stored_results() <= r or settings.sort:
            # Need more results
            return redirect_to_pending(corpus.id)
    settings.need_query_rerun(False)
    if settings.sort:
        sort_column = dict(
            lc=poliqarp.LeftContextType,
            lm=poliqarp.LeftMatchType,
            rm=poliqarp.RightMatchType,
            rc=poliqarp.RightContextType,
        )[settings.sort_column]
        connection.sort(sort_column, settings.sort_type == 'atergo', settings.sort_direction == 'asc')
    del settings.sort, settings.sort_column, settings.sort_atergo, settings.sort_ascending
    settings.need_sort_rerun(False)
    n_results = connection.get_n_stored_results()
    l = max(l, 0)
    r = min(r, n_results - 1)
    if l > r > 0:
        raise django.http.Http404
    qinfo.l = 1 + l
    qinfo.r = 1 + r
    if l > 0:
        page_size = min(l, settings.results_per_page)
        prev_l = l - page_size
        qinfo.prev_page = PageInfo(corpus.id, page_start=prev_l, n=page_size)
    if n_results > r + 1:
        page_size = n_results - r - 1
        if page_size > settings.results_per_page or qinfo.running:
            page_size = settings.results_per_page
        qinfo.next_page = PageInfo(corpus.id, page_start=r+1, n=page_size)
    qinfo.results = connection.get_results(l, r)
    qinfo.n_stored_results = connection.get_n_stored_results()
    return qinfo

class Connection(poliqarp.Connection):

    def __init__(self, extra):
        poliqarp.Connection.__init__(self)
        self.__extra = extra

    def get_default_session_name(self):
        return '%s/%s' % (poliqarp.Connection.get_default_session_name(self), self.__extra)

def setup_settings(request, settings, connection):
    del settings.results_per_page # Never need to be dirty
    locale = utils.i18n.get_locale(request.LANGUAGE_CODE)
    connection.set_locale(locale)
    del settings.language
    connection.set_retrieve_ids(0, 1, 1, 0)
    # These settings are ignored a retrieve level:
    connection.set_retrieve_lemmata(1, 1, 1, 1)
    connection.set_retrieve_tags(1, 1, 1, 1)
    del settings.show_in_context
    del settings.show_in_match
    connection.set_left_context_width(settings.left_context_width)
    connection.set_right_context_width(settings.right_context_width)
    connection.set_wide_context_width(settings.wide_context_width)
    del settings.left_context_width
    del settings.right_context_width
    del settings.wide_context_width
    connection.set_random_sample(settings.random_sample)
    del settings.random_sample

class Result(object):

    def __init__(self, corpus, n, raw_result, settings):
        self._raw_result = list(raw_result)
        self.n = n
        self.url = django.core.urlresolvers.reverse(
            process_query,
            kwargs=dict(corpus_id=corpus.id, nth=n)
        )
        for column in self._raw_result:
            ctype = column[0]
            if ctype.is_match:
                ctype.show_lemmata = 'l' in settings.show_in_match
                ctype.show_tags = 't' in settings.show_in_match
            elif ctype.is_context:
                ctype.show_lemmata = 'l' in settings.show_in_context
                ctype.show_tags = 't' in settings.show_in_context

    def __getitem__(self, n):
        return self._raw_result[n]

    def __iter__(self):
        return iter(self._raw_result)

def enhance_columns(results, settings):
    for result in results:
        result.enhance_columns(settings)

def get_traceback(exc_info=None):
    '''Helper function to return the traceback as a string'''
    import traceback
    return '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))

def report_invalid_session_id(request, exc_info):
    subject = 'Invalid session id (%s IP): %s' % (
        request.META.get('REMOTE_ADDR') in django.conf.settings.INTERNAL_IPS and 'internal' or 'EXTERNAL',
        request.path
    )
    try:
        request_repr = repr(request)
    except:
        request_repr = "Request repr() unavailable"
    message = "%s\n\n%s" % (get_traceback(exc_info), request_repr)
    django.core.mail.mail_admins(subject, message)

@contextlib.contextmanager
def connection_for(request, settings):
    with utils.locks.SessionLock(request.session):
        connection = request.session.get('connection')
        if connection is None:
            connection = Connection(extra=request.session.session_key)
            request.session['connection'] = connection
        try:
            try:
                if connection.make_session():
                    setup_settings(request, settings, connection)
                    settings.need_query_rerun(True)
                elif settings.dirty():
                    setup_settings(request, settings, connection)
            except (poliqarp.errors.InvalidSessionId, poliqarp.errors.InvalidSessionUserId):
                # Forget about this connection
                del request.session['connection']
                request.session.save()
                connection.close()
                report_invalid_session_id(request, sys.exc_info())
                # Create a new one
                connection = Connection(extra=request.session.session_key)
                request.session['connection'] = connection
                connection.make_session()
                setup_settings(request, settings, connection)
                settings.need_query_rerun(True)
            yield connection
            connection.suspend_session()
        finally:
            connection.close()
        request.session.save()

def corpus_info(request, corpus_id):
    template = get_template('corpus-info.html')
    form = QueryForm()
    request.session.set_test_cookie()
    corpus = get_corpus_by_id(corpus_id)
    context = Context(request, selected=corpus, form=form)
    try:
        extra_template = django.template.loader.get_template('corpora/%s.html' % corpus.id)
        corpus_info = extra_template.render(context)
    except django.template.TemplateDoesNotExist:
        corpus_info = None
    context.update(dict(corpus_info=corpus_info))
    response = django.http.HttpResponse(template.render(context))
    return response

def process_query(request, corpus_id, query=False, page_start=0, nth=None):
    settings = get_settings(request)
    template = get_template('query.html')
    corpus = get_corpus_by_id(corpus_id)
    if settings.need_query_rerun() and nth is not None:
        url = django.core.urlresolvers.reverse(
            process_query,
            kwargs=dict(corpus_id=corpus.id)
        )
        return django.http.HttpResponseRedirect(url)
    error = None
    qinfo = None
    form_data = None
    if request.method == 'POST':
        form_data = request.POST
        if not request.session.test_cookie_worked():
            error = ugettext_lazy('Please enable cookies and try again')
    elif query:
        query = request.session.get('query')
        if query is not None:
            form_data = dict(query=query)
    form = QueryForm(form_data)
    request.session.set_test_cookie()
    if form_data is not None and form.is_valid() and error is None:
        query = form.cleaned_data['query']
        request.session['query'] = query
        if nth is not None:
            nth = int(nth)
            l = (nth // settings.results_per_page) * settings.results_per_page
        else:
            l = int(page_start or 0)
        r = l + settings.results_per_page - 1
        with connection_for(request, settings) as connection:
            if request.method == 'POST' and settings.random_sample:
                # With random sample on, rerunning query makes sense
                # even if query text didn't change
                settings.need_query_remake(True)
            qinfo = run_query(connection, settings, corpus, query, l, r)
            if nth is not None:
                qinfo.rinfo = extract_result_info(connection, settings, corpus, nth)
        if isinstance(qinfo, Exception):
            error = qinfo
            qinfo = None
        elif isinstance(qinfo, django.http.HttpResponseRedirect):
            return qinfo
        else:
            qinfo.results = [Result(corpus, l + i, result, settings) for (i, result) in enumerate(qinfo.results)]
            if nth is not None:
                qinfo.result = qinfo.results[qinfo.rinfo.n - l]
            corpus.enhance_results(qinfo.results)
    if error is not None:
        form._errors.setdefault('query', form.error_class()).append(error)
    context = Context(request, selected=corpus, form=form, qinfo=qinfo)
    response = django.http.HttpResponse(template.render(context))
    response['Refresh'] = str(global_settings.SESSION_REFRESH)
    return response

def process_metadata_snippet(request, corpus_id, nth):
    settings = get_settings(request)
    template = get_template('result-metadata.html')
    corpus = get_corpus_by_id(corpus_id)
    nth = int(nth)
    with connection_for(request, settings) as connection:
        rinfo = extract_result_info(connection, settings, corpus, nth)
    context = Context(request, qinfo=dict(rinfo=rinfo))
    return django.http.HttpResponse(template.render(context))

class SettingsForm(django.forms.Form):
    random_sample = django.forms.BooleanField(required=False)
    random_sample_size = django.forms.IntegerField(
        min_value=1,
        max_value=global_settings.MAX_RANDOM_SAMPLE_SIZE,
        widget=django.forms.TextInput(attrs=dict(size=3))
    )
    sort = django.forms.BooleanField(required=False)
    sort_column = django.forms.ChoiceField(
        choices=[
            ('lc', ugettext_lazy('by left context')),
            ('lm', ugettext_lazy('by left match')),
            ('rm', ugettext_lazy('by right match')),
            ('rc', ugettext_lazy('by right context')),
        ],
        widget=django.forms.RadioSelect
    )
    sort_type = django.forms.ChoiceField(
        choices = [
            ('afronte', ugettext_lazy('a fronte')),
            ('atergo', ugettext_lazy('a tergo')),
        ],
        widget=django.forms.RadioSelect
    )
    sort_direction = django.forms.ChoiceField(
        choices = [
            ('asc', ugettext_lazy('ascending')),
            ('desc', ugettext_lazy('descending')),
        ],
        widget=django.forms.RadioSelect
    )
    show_in_context = django.forms.ChoiceField(
        choices = [
            ('slt', ugettext_lazy('segments, lemmata and tags')),
            ('sl', ugettext_lazy('segments and lemmata')),
            ('s', ugettext_lazy('segments only')),
        ],
        widget=django.forms.RadioSelect
    )
    show_in_match = django.forms.ChoiceField(
        choices = [
            ('slt', ugettext_lazy('segments, lemmata and tags')),
            ('sl', ugettext_lazy('segments and lemmata')),
            ('s', ugettext_lazy('segments only')),
        ],
        widget=django.forms.RadioSelect
    )
    left_context_width = django.forms.IntegerField(
        min_value = 1,
        max_value = poliqarp.MAX_CONTEXT_SEGMENTS,
        widget=django.forms.TextInput(attrs=dict(size=2))
    )
    right_context_width = django.forms.IntegerField(
        min_value = 1,
        max_value = poliqarp.MAX_CONTEXT_SEGMENTS,
        widget=django.forms.TextInput(attrs=dict(size=2))
    )
    wide_context_width = django.forms.IntegerField(
        min_value = 1,
        max_value = poliqarp.MAX_WCONTEXT_SEGMENTS,
        widget=django.forms.TextInput(attrs=dict(size=3))
    )
    results_per_page = django.forms.IntegerField(
        min_value = 1,
        max_value = global_settings.MAX_RESULTS_PER_PAGE,
        widget=django.forms.TextInput(attrs=dict(size=3))
    )
    next = django.forms.CharField(
        required=False,
        widget=django.forms.HiddenInput
    )

class Settings(object):

    defaults = dict(
        language = None,
        random_sample = 0,
        random_sample_size = 50,
        sort = False,
        sort_column = 'rm',
        sort_type = 'afronte',
        sort_direction = 'asc',
        show_in_match = 'slt',
        show_in_context = 's',
        left_context_width = 5,
        right_context_width = 5,
        wide_context_width = 50,
        results_per_page = 25,
    )

    _dirty = set()
    def dirty(self, key=None):
        if key is None:
            return frozenset(self._dirty)
        else:
            return key in self._dirty

    def __delattr__(self, key):
        if key in self._dirty:
            self._dirty.remove(key)

    def __getattr__(self, key):
        if key in self.defaults:
            value = self.defaults[key]
            object.__setattr__(self, key, value)
            return value
        if key.startswith('dirty_'):
            return lambda key=key: self.dirty(key[6:])
        elif key.startswith('clean_'):
            return lambda key=key: self.clean(key[6:])
        raise AttributeError

    def __setattr__(self, key, value):
        if key.startswith('_'):
            return object.__setattr__(self, key, value)
        if value != getattr(self, key):
            try:
                callback = getattr(type(self), 'on_set_%s' % key)
            except AttributeError:
                pass
            else:
                callback(self, key, value)
        object.__setattr__(self, key, value)
        self._dirty.add(key)

    _need_query_remake = False
    def need_query_remake(self, value=None):
        if value is not None:
            self._need_query_remake = value
        return self._need_query_remake

    _need_query_rerun = False
    def need_query_rerun(self, value=None):
        if value is not None:
            self._need_query_rerun = value
        return self._need_query_rerun

    _need_sort_rerun = False
    def need_sort_rerun(self, value=None):
        if value is not None:
            self._need_sort_rerun = value
        return self._need_sort_rerun

    def get_dict(self):
        return dict((key, getattr(self, key)) for key in self.defaults)

    def on_set_random_sample(self, key, value):
        self._need_query_rerun = True
        self._need_query_remake = True

    def on_set_random_sample_size(self, key, value):
        if self.random_sample:
            self._need_query_rerun = True

    def on_set_sort(self, key, value):
        if value == True:
            self._need_query_resort = True

    def on_sort_ex(self, key, value):
        if self.sort:
            self.need_query_resort = True
    on_sort_column = on_sort_type = on_sort_direction = on_sort_ex

    def __repr__(self):
        return '<%s.%s with %s>' % (
            self.__module__,
            type(self).__name__,
            ', '.join('%s=%r' % (key, getattr(self, key)) for key in type(self).defaults)
        )

def get_referrer(request):
    referrer = request.META.get('HTTP_REFERER', '')
    prefix = request.build_absolute_uri('/')
    if referrer.startswith(prefix):
        return referrer[len(prefix)-1:]

def get_settings(request):
    settings = request.session.get('settings')
    if settings is None:
        settings = Settings()
        request.session['settings'] = settings
    return settings

def process_settings(request):
    template = get_template('settings.html')
    context = Context(request, selected='settings')
    form_data = None
    settings = get_settings(request)
    if settings is None:
        settings = Settings()
    next = None
    if request.method == 'POST':
        form_data = request.POST.copy()
        next = form_data.get('next')
    else:
        form_data = settings.get_dict()
    next = next or get_referrer(request)
    form_data['next'] = next
    form = SettingsForm(form_data)
    if form.is_valid() and request.method == 'POST':
        for key, value in form.cleaned_data.iteritems():
            if key == 'next':
                continue
            setattr(settings, key, value)
        request.session.save()
        if next:
            return django.http.HttpResponseRedirect(next)
    context = Context(request, form=form, selected='settings')
    return django.http.HttpResponse(template.render(context))

def set_language(request):
    '''
    Redirect to a given URL while setting the chosen language in the
    session or cookie. The URL and the language code need to be
    specified in the request parameters.

    Since this view changes how the user will see the rest of the site, it must
    only be accessed as a POST request. If called as a GET request, it will
    redirect to the page in the request (the 'next' parameter) without changing
    any state.
    '''
    url = request.REQUEST.get('next', None) or get_referrer(request) or '/'
    response = django.http.HttpResponseRedirect(url)
    if request.method == 'POST':
        lang_code = request.POST.get('language', None)
        if lang_code and django.utils.translation.check_for_language(lang_code):
            get_settings(request).language = lang_code
            request.session['django_language'] = lang_code
            request.session.save()
    return response

def process_help(request):
    template = get_template('help.html')
    help_urls = [
        'http://korpus.pl/%(lang)s/cheatsheet/' % dict(lang=request.LANGUAGE_CODE),
        'http://poliqarp.sourceforge.net/man/poliqarp-query-syntax.html',
    ]
    context = Context(request, selected='help', help_urls=help_urls)
    return django.http.HttpResponse(template.render(context))

def process_cheatsheet(request):
    url = 'http://korpus.pl/%(lang)s/cheatsheet/' % dict(lang=request.LANGUAGE_CODE)
    return django.http.HttpResponseRedirect(url)

def process_ping(request):
    if not django.conf.settings.DEBUG:
        raise django.http.Http404
    with utils.locks.SessionLock(request.session):
        connection = request.session.get('connection')
        if connection is None:
            connection = Connection(extra=request.session.session_key)
        with connection:
            connection.make_session()
            t1 = time.time()
            connection.ping()
            t2 = time.time()
        response = django.http.HttpResponse('%.2f ms' % ((t2 - t1) * 1000))
        response['Content-Type'] = 'text/plain'
        return response

# vim:ts=4 sw=4 et
