import operator
from . import operator as uoperator


infinity = float('inf')
NaN = float('NaN')


def minmax(*args, **kwargs):
	keyfn = kwargs.get('key')
	if isinstance(keyfn, str):
		keyfn = operator.attrgetter(keyfn)

	iterator = iter(args if len(args) > 1 else args[0])
	min_item = next(iterator)
	max_item = min_item
	if keyfn is None:
		for item in iterator:
			if max_item < item:
				max_item = item
			elif item < min_item:
				min_item = item
	else:
		min_value = keyfn(min_item)
		max_value = min_value
		for item in iterator:
			value = keyfn(item)
			if max_value < value:
				max_value = value
				max_item = item
			elif value < min_value:
				min_value = value
				min_item = item
	return min_item, max_item


def minmax2(a, b, key=uoperator.identity, reverse=False):
	"""Guarantees the return of two distinct values iff a is not b."""
	if isinstance(key, str):
		key = operator.attrgetter(key)
	return (a, b) if (key(a) <= key(b)) is not reverse else (b, a)


def sliceout(sequence, start, end=None):
	if end is None:
		end = start + 1
	return sequence[:start] + sequence[end:]


def starmap(function, iterable):
	return [function(*item) for item in iterable]


def issubset(iterable, set):
	return all(map(set.__contains__, iterable))


def rdict(d):
	if isinstance(d, dict):
		d = d.items()
	if __debug__:
		d = frozenset(d)
	rdict = {v: k for k, v in d}
	assert len(rdict) == len(d) # future keys should be unique
	return rdict


def min_index(*args, **kwargs):
	key = kwargs.get('key')
	kwargs['key'] = args.__getitem__ if key is None else lambda idx: key(args[idx])
	return min(*range(len(args)), **kwargs)


class NonLocal:

	def __init__(self, value=None):
		self.value = value


def setattr_default(obj, attr, value):
	if hasattr(obj, attr):
		return getattr(obj, attr)
	else:
		setattr(obj, attr, value)
		return value
