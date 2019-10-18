import importlib


def parse(src):
	try:
		if src == ':':
			from ..description import default as desc
		elif src.startswith(':'):
			desc = importlib.import_module(src[1:], __package__.partition('.')[0])
		else:
			desc = importlib.machinery.SourceFileLoader(src, src).load_module()
	except:
		raise ImportError(src)

	if not getattr(desc, 'descriptions', None):
		raise NameError(
			"The collector description module doesn't contain any collector description.",
			desc, desc.__file__,
			"missing attribute 'descriptions'")

	return desc
