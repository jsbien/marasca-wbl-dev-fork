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

import array
import os
import sys
from cStringIO import StringIO

import django.http
import django.conf

import cairo

import djvu.decode

from .views import get_corpus_by_id

screen_dpi = django.conf.settings.SNIPPET_DEFAULT_SCREEN_DPI
snippet_max_width = django.conf.settings.SNIPPET_MAX_WIDTH
snippet_max_height = django.conf.settings.SNIPPET_MAX_HEIGHT
snippet_colors = django.conf.settings.SNIPPET_COLORS

djvu_pixel_format = djvu.decode.PixelFormatRgbMask(0xff << 16, 0xff << 8, 0xff, bpp=32)
djvu_pixel_format.rows_top_to_bottom = 1
djvu_pixel_format.y_top_to_bottom = 0

class Context(djvu.decode.Context):

    def __init__(self, *args, **kwargs):
        djvu.decode.Context.__init__(self, *args, **kwargs)
        self.cache_size = django.conf.settings.SNIPPET_CACHE_SIZE

    def handle_message(self, message):
        if isinstance(message, djvu.decode.ErrorMessage):
            print >>sys.stderr, message

    def render_snippet(self, path, page, x, y, w, h):
        document = self.new_document(djvu.decode.FileURI(path))
        document.decoding_job.wait()
        try:
            page_job = document.pages[page - 1].decode(wait=True)
        except IndexError:
            raise django.http.Http404

        page_width, page_height = page_job.size
        dpi = page_job.dpi

        pw, ph = (i * screen_dpi // dpi for i in (page_width, page_height))
        hx, hy, hw, hh = (i * screen_dpi // dpi for i in (x, y, w, h))

        sx, sy, sw, sh = x, y, w, h
        cropped_highlight = (
            # A different color will be used for a (partially) cropped
            # highlight.
            sw > snippet_max_width * dpi // screen_dpi or
            sh > snippet_max_height * dpi // screen_dpi
        )
        sy -= sh // 2
        sh *= 2
        # Correct dimensions, so that the resulting image width is equal to
        # SNIPPET_MAX_WIDTH:
        dx = sw - snippet_max_width * dpi // screen_dpi
        sx += dx // 2
        sw -= dx
        if sh > snippet_max_height * dpi // screen_dpi:
            # Correct dimensions, so that the resulting image is not higher than
            # SNIPPET_MAX_HEIGHT:
            dy = sh - snippet_max_height * dpi // screen_dpi
            sy += dy // 2
            sh -= dy

        sx, sy, sw, sh = (i * screen_dpi // dpi for i in (sx, sy, sw, sh))
        rx, ry, rw, rh = sx, sy, sw, sh

        if rx < 0:
            rw += rx
            rx = 0
        if rx + rw > pw:
            rw = pw - rx
        if ry < 0:
            rh += ry
            ry = 0
        if ry + rh > ph:
            rh = ph - ry
        if rw <= 0 or rh <= 0:
            raise django.http.Http404

        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_RGB24, rw)
        data = page_job.render(djvu.decode.RENDER_COLOR,
            (0, 0, pw, ph), (rx, ry, rw, rh),
            djvu_pixel_format, stride
        )
        data = array.array('B', data)
        fp = StringIO()
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh)
        djvu_surface = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_RGB24, rw, rh, stride)
        cc = cairo.Context(surface)
        cc.set_source_surface(djvu_surface, rx - sx, ry - sy)
        cc.paint()
        cc.set_source_rgba(*snippet_colors[cropped_highlight])
        cc.rectangle(hx - sx, hy - sy, hw, hh)
        cc.fill()
        surface.write_to_png(fp)
        fp.seek(0)
        return fp

context = Context()

def view(request, corpus_id, volume, page, x, y, w, h):
    corpus = get_corpus_by_id(corpus_id)
    volume, page, x, y, w, h = map(int, (volume, page, x, y, w, h))
    try:
        djvu_directory = corpus.djvu_directory
    except AttributeError:
        raise django.http.Http404
    for padding in range(1, 10):
        djvu_filename = os.path.join(djvu_directory, '%0*d' % (padding, volume), 'index.djvu')
        if os.path.exists(djvu_filename):
            break
    else:
        # If the file didn't exist, we'd get an unhelpful message from DjVuLibre.
        # Make sure that the file exist _before_ calling any DjVuLibre API.
        raise django.http.Http404
    image = context.render_snippet(djvu_filename, page, x, y, w, h)
    response = django.http.HttpResponse(image)
    response['Content-Type'] = 'image/png'
    return response

# vim:ts=4 sw=4 et
