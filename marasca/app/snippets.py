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
        sy -= sh // 2
        sh *= 2
        dx = sw - snippet_max_width * dpi // screen_dpi
        sx += dx // 2
        sw -= dx
        if sh > snippet_max_height:
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
        cc.set_source_rgba(0, 0, 1, 0.25)
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
    djvu_filename = os.path.join(djvu_directory, '%02d' % volume, 'index.djvu')
    image = context.render_snippet(djvu_filename, page, x, y, w, h)
    response = django.http.HttpResponse(image)
    response['Content-Type'] = 'image/png'
    return response

# vim:ts=4 sw=4 et
