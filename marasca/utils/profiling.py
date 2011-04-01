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
