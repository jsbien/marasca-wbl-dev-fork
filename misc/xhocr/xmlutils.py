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
XML utilities
'''

import copy
import re

import lxml.etree as etree

namespaces = dict(
    xhtml='http://www.w3.org/1999/xhtml'
)

def repr(elem):
    '''
    returns human-readable representation of the element (without its contents)
    '''
    elem = copy.copy(elem)
    elem[:] = []
    elem.text = None
    elem.tail = None
    s = etree.tostring(elem)
    assert s[-2:] == '/>'
    return s[:-2] + '>'

def location(elem):
    '''
    returns human-readable representation of the XML element location
    '''
    path = elem.getroottree().docinfo.URL
    n = elem.sourceline
    return '{path}:{n}'.format(path=path, n=n)

def elem_inside_to_string(elem):
    s = etree.tostring(elem, with_tail=False)
    s = re.sub('^<[^>]*>', '', s, count=1)
    s = re.sub('</[^>]*>$', '', s, count=1)
    return s

# vim:ts=4 sw=4 et
