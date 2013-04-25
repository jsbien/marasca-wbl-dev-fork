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

'''BCP-47 support'''

# https://code.google.com/p/tesseract-ocr/issues/detail?id=878#c4

_tesseract_to_bcp47 = r'''
afr af
ara ar
aze az
bel be
ben bn
bul bg
cat ca
ces cs
chi_sim zh-Hans
chi_tra zh-Hant
dan da
dan-frak da-Latf
deu de
deu-frak de-Latf
ell el
eng en
epo eo
est et
eus eu
fin fi
fra fr
glg gl
heb he
hin hi
hrv hr
hun hu
ind id
isl is
ita it
jpn ja
kan kn
kor ko
lav lv
lit lt
mal ml
mkd mk
mlt mt
msa ms
nld nl
nor no
pol pl
por pt
ron ro
rus ru
slk sk
slk-frak sk-Latf
slv sl
spa es
sqi sq
srp sr
swa sw
swe sv
tam ta
tel te
tgl tl
tha th
tur tr
ukr uk
vie vi
'''

_tesseract_to_bcp47 = dict(
	line.split()
    for line in _tesseract_to_bcp47.strip().splitlines()
)

def from_tesseract(lang):
    '''
    convert from Tesseract language codes to BCP-47
    '''
    return _tesseract_to_bcp47.get(lang, lang)

# vim:ts=4 sw=4 et
