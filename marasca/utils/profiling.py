import sys
import cProfile

from django.conf import settings

class ProfilingMiddleware(object):

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if not 'profile' in request.GET:
            return
        self.profiler = cProfile.Profile()
        args = (request,) + callback_args
        return self.profiler.runcall(callback, *args, **callback_kwargs)

    def process_response(self, request, response):
        if not 'profile' in request.GET:
            return response
        self.profiler.create_stats()
        response.content = ''
        old_stdout, sys.stdout = sys.stdout, response
        self.profiler.print_stats(1)
        sys.stdout = old_stdout
        response['Content-type'] = 'text/plain; charset=US-ASCII'
        return response

# vim:ts=4 sw=4 et
