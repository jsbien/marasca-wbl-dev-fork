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

from __future__ import print_function

# http://www.iana.org/assignments/language-subtag-registry
# 2013-02-28
_suppress_script = r'''
ab Cyrl
af Latn
am Ethi
ar Arab
as Beng
ay Latn
be Cyrl
bg Cyrl
bn Beng
bs Latn
ca Latn
ch Latn
cs Latn
cy Latn
da Latn
de Latn
dv Thaa
dz Tibt
el Grek
en Latn
eo Latn
es Latn
et Latn
eu Latn
fa Arab
fi Latn
fj Latn
fo Latn
fr Latn
fy Latn
ga Latn
gl Latn
gn Latn
gu Gujr
gv Latn
he Hebr
hi Deva
hr Latn
ht Latn
hu Latn
hy Armn
id Latn
in Latn
is Latn
it Latn
iw Hebr
ja Jpan
ka Geor
kk Cyrl
kl Latn
km Khmr
kn Knda
ko Kore
la Latn
lb Latn
ln Latn
lo Laoo
lt Latn
lv Latn
mg Latn
mh Latn
mk Cyrl
ml Mlym
mo Latn
mr Deva
ms Latn
mt Latn
my Mymr
na Latn
nb Latn
nd Latn
ne Deva
nl Latn
nn Latn
no Latn
nr Latn
ny Latn
om Latn
or Orya
pa Guru
pl Latn
ps Arab
pt Latn
qu Latn
rm Latn
rn Latn
ro Latn
ru Cyrl
rw Latn
sg Latn
si Sinh
sk Latn
sl Latn
sm Latn
so Latn
sq Latn
ss Latn
st Latn
sv Latn
sw Latn
ta Taml
te Telu
th Thai
ti Ethi
tl Latn
tn Latn
to Latn
tr Latn
ts Latn
uk Cyrl
ur Arab
ve Latn
vi Latn
xh Latn
yi Hebr
zu Latn
dsb Latn
frr Latn
frs Latn
gsw Latn
hsb Latn
kok Deva
mai Deva
men Latn
nds Latn
niu Latn
nqo Nkoo
nso Latn
tem Latn
tkl Latn
tmh Latn
tpi Latn
tvl Latn
zbl Blis
'''

_suppress_script = dict(
	line.split()
    for line in _suppress_script.strip().splitlines()
)

def _update_suppress_script():
    tagtype = subtag = script = None
    url = 'http://www.iana.org/assignments/language-subtag-registry'
    print('# {url}'.format(url=url))
    first = True
    import urllib2
    import contextlib
    with contextlib.closing(urllib2.urlopen(url)) as file:
        for line in file:
            line = line.rstrip('\n')
            if line == '%%':
                if tagtype == 'language':
                    assert subtag is not None
                    if script is not None:
                        if first:
                            print("_suppress_script = r'''")
                            first = False
                        print(subtag, script)
                tagtype = subtag = script = None
            else:
                if line.startswith(' '):
                    continue
                key, value = map(str.strip, line.split(':', 1))
                if key == 'File-Date':
                    print('# {date}'.format(date=value))
                elif key == 'Type':
                    assert tagtype is None
                    tagtype = value
                elif key == 'Subtag':
                    assert subtag is None
                    subtag = value
                elif key == 'Suppress-Script':
                    assert script is None
                    script = value
    print("'''")

class LanguageTag(object):

    def __init__(self, tag):
        self.tag = tag
        subtags = tag.split('-')
        # TODO: add support for grandfathered tags
        if subtags[0] == 'x':
            self.language = tag
        else:
            self.language = subtags[0].lower()
            self.script = None
            for subtag in subtags[1:]:
                if len(subtag) == 1:
                    break
                if len(subtag) == 4:
                    self.script = subtag[0].upper() + subtag[1:].lower()
            if self.script is None:
                self.script = _suppress_script.get(self.language)

    @classmethod
    def from_tesseract(cls, lang):
        '''
        convert from Tesseract language codes to BCP-47
        '''
        return cls(_tesseract_to_bcp47.get(lang, lang))

    def get_locale(self):
        '''
        return locale object for UAX#29
        '''
        import uax29
        return uax29.Locale(self.tag)

    def __str__(self):
        return self.tag

    def __repr__(self):
        return '{mod}.{cls}({tag!r})'.format(
            mod=self.__module__,
            cls=type(self).__name__,
            tag=self.tag
        )

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

if __name__ == '__main__':
    _update_suppress_script()

# vim:ts=4 sw=4 et
