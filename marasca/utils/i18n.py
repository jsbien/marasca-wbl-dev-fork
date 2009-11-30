_locale_map = dict(
	en = 'en_US',
	pl = 'pl_PL',
)

_default_locale = 'en_US'

def get_locale(language_code):
	# FIXME: Move handling of .UTF-8 suffix into poliqarpd
	return _locale_map.get(language_code, _default_locale) + '.UTF-8'

# vim:ts=4 sw=4 noet
