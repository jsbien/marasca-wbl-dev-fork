# encoding=UTF-8

# Copyright © 2013 Jakub Wilk <jwilk@jwilk.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 dated June, 1991.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.

'''
hOCR format support
'''

import copy
import re

import bcp47
import logger
import uax29
import xmlutils

bbox_re = re.compile(ur'\b bbox \s+ (\d+) \s+ (\d+) \s+ (\d+) \s+ (\d+) \b', re.VERBOSE)
wconf_re = re.compile(ur'\b x_wconf \s+ (\d+) \b', re.VERBOSE)

def parse_title(elem):
    title = elem.get('title', '')
    orc = u'\N{OBJECT REPLACEMENT CHARACTER}'
    bbox_match = bbox_re.search(title)
    bbox = [int(x) for x in bbox_match.groups()]
    wconf_match = wconf_re.search(title)
    wconf = int(wconf_match.groups()[0])
    title = bbox_re.sub(orc, title)
    title = wconf_re.sub(orc, title)
    return title, bbox, wconf

def subst_bbox(elem, bbox):
    title = elem.get('title')
    if not title:
        return
    bbox = 'bbox {0} {1} {2} {3}'.format(*bbox)
    title = bbox_re.sub(bbox, title, count=1)
    elem.set('title', title)

class MergeError(Exception):
    pass

class Merger(object):

    def __init__(self, options):
        self.options = options

    def merge(self, elements):
        elements = list(elements)
        base_element = elements[0]
        base_attribs = dict(base_element.attrib)
        for element in elements:
            classes = frozenset(element.get('class', '').split())
            ocr_word = 'ocrx_word' in classes
            ocr_page = 'ocr_page' in classes
            ocr_line = 'ocr_line' in classes
            if (element.prefix, element.tag) != (base_element.prefix, base_element.tag):
                logger.logger.error("error: unable to merge hOCR because element names differ:")
                for e in base_element, element:
                    logger.error('- {loc}: {elem}',
                        loc=xmlutils.location(e),
                        elem=xmlutils.repr(e),
                    )
                raise MergeError
            if not ocr_word and element.text != base_element.text:
                logger.error("error: unable to merge hOCR because element's texts differ:")
                for e in base_element, element:
                    logger.error('- {loc}: {elem} text {text!r}',
                        loc=xmlutils.location(e),
                        elem=xmlutils.repr(e),
                        text=e.text,
                    )
                raise MergeError
            if element.tail != base_element.tail:
                logger.error("error: unable to merge hOCR because texts after the elements differ:")
                for e in base_element, element:
                    logger.error('- {loc}: {elem} text {text!r}',
                        loc=xmlutils.location(e),
                        elem=xmlutils.repr(e),
                        text=e.tail,
                    )
                raise MergeError
            attrs_to_check = sorted(set(base_attribs) | set(element.keys()))
            for attr in attrs_to_check:
                if element.get(attr) != base_element.get(attr):
                    if ocr_page and attr == 'title':
                        continue
                    if ocr_word and attr in ('id', 'dir', 'lang', 'title'):
                        continue
                    logger.error("error: unable to merge hOCR because attributes differ")
                    for e in base_element, element:
                        logger.error('- {loc}: {elem} attribute {key!r} is {value!r}',
                            loc=xmlutils.location(e),
                            elem=xmlutils.repr(e),
                            key=attr,
                            value=e.get(attr),
                        )
                    raise MergeError
            if not ocr_word and len(element) != len(base_element):
                if ocr_line:
                    logfn = logger.warning
                    logfn("warning: number of child elements didn't match:")
                else:
                    logfn = logger.error
                    logfn("error: unable to merge hOCR because number of child elements didn't match:")
                for e in base_element, element:
                    logfn('- {loc}: {elem} has {n} {child}',
                        loc=xmlutils.location(e),
                        elem=xmlutils.repr(e),
                        n=len(e),
                        child=('child' if len(e) == 1 else 'children'),
                    )
                if ocr_line:
                    return
                else:
                    raise MergeError
        if ocr_word:
            return self.merge_words(elements)
        for group in zip(*elements):
            self.merge(group)
        return base_element

    @classmethod
    def get_text_element(cls, element):
        # TODO: add sanity checks
        while len(element) == 1:
            [element] = element
        return element

    @classmethod
    def get_text(cls, element):
        return (cls.get_text_element(element).text or '').strip()

    def merge_words(self, elements):
        elements = list(elements)
        base_element = elements[0]
        base_title_pattern = parse_title(base_element)[0]
        max_wconf = -1
        max_element = None
        for element in elements:
            try:
                del element.attrib['id'] # merging could cause duplicate identifiers
            except LookupError:
                pass
            title_pattern, bbox, wconf = parse_title(element)
            if title_pattern != base_title_pattern:
                logger.error("error: unable to merge hOCR because attributes differ")
                for e in base_element, element:
                    logger.error("- {loc}: {elem} attribute 'title' is {value!r}",
                        loc=xmlutils.location(e),
                        elem=xmlutils.repr(e),
                        value=e.get('title'),
                    )
            # TODO: check if bounding boxes are matching
            if wconf > max_wconf:
                max_wconf = wconf
                max_element = element
        base_parent = base_element.getparent()
        if max_element is not base_element:
            base_parent.replace(base_element, max_element)
        lang = max_element.get('lang')
        if lang:
            lang = bcp47.from_tesseract(lang)
            if self.options.uax29:
                locale = uax29.Locale(lang)
            if self.options.fix_lang:
                max_element.set('lang', lang)
        elif self.options.uax29:
            locale = uax29.default_locale
        text_element = self.get_text_element(max_element)
        text = (text_element.text or '').strip()
        if not text:
            # TODO: Implement a better strategy for dealing with empty words.
            logger.warning('warning: empty word')
            logger.warning("- {loc}: {elem}",
                loc=xmlutils.location(max_element),
                elem=xmlutils.repr(max_element),
            )
            return
        if not self.options.uax29:
            return
        split_text = list(uax29.split_bbox(text, bbox, locale=locale))
        if len(split_text) > 1:
            for subtext, subbbox in split_text:
                subelement = copy.deepcopy(max_element)
                subtext_element = self.get_text_element(subelement)
                subtext_element.text = subtext
                subst_bbox(subelement, subbbox)
                subelement.tail = None
                max_element.addprevious(subelement)
            subelement.tail = max_element.tail
            base_parent.remove(max_element)

# vim:ts=4 sw=4 et
