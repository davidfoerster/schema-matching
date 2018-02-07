import itertools, operator
from . import functional as ufunctional


if __debug__:
	import builtins

	def map(*args):
		return tuple(builtins.map(*args))

	def zip(*args):
		return tuple(builtins.zip(*args))

	def filter(function, iterable):
		return tuple(builtins.filter(function, iterable))

	def filterfalse(function, iterable):
		return tuple(itertools.filterfalse(function, iterable))

else:
	from builtins import map, filter, zip
	from itertools import filterfalse



__iterator_cookie = object()


def each(function, *iterables):
	if not iterables:
		return
	elif len(iterables) == 1:
		for args in iterables[0]:
			function(args)
	else:
		stareach(function, zip(*iterables))


def stareach(function, iterable):
	for args in iterable:
		function(*args)


def consume(iterable):
	iterator = iter(iterable)
	while next(iterator, __iterator_cookie) is not __iterator_cookie:
		pass


def __slice_to_tuple(slice):
	return (slice.start, slice.stop, slice.step)


def islice(iterable, *args):
	if not args:
		args = (None,)
	elif len(args) == 1 and isinstance(args[0], slice):
		args = __slice_to_tuple(args[0])
	return itertools.islice(iterable, *args)


def map_inplace(function, list, depth=0, slice=None):
	if depth <= 0:
		if slice is None:
			list[:] = map(function, list)
		else:
			list[slice] = map(function,
				itertools.islice(list, slice.start, slice.stop, slice.step))
	else:
		for item in list:
			map_inplace(function, item, depth - 1, slice)
	return list


def countif(function, *iterables):
	return sum(map(bool, itertools.starmap(function, *iterables)))


def teemap(iterable, *functions):
	return map(lambda item: [item if f is None else f(item) for f in functions], iterable)


def issorted(iterable, key=None, reverse=False):
	if key is not None:
		iterable = map(key, iterable)
	it = iter(iterable)
	last_item_key = next(it, __iterator_cookie)
	if last_item_key is not __iterator_cookie:
		not_in_order = operator.lt if reverse else operator.gt
		for item_key in it:
			if not_in_order(last_item_key, item_key):
				return False
			last_item_key = item_key
	return True


def order(sequence, key=None, reverse=False):
	key2 = sequence.__getitem__
	if key is not None:
		key2 = ufunctional.composefn(key2, key)
	order = list(range(len(sequence)))
	order.sort(key=key2, reverse=reverse)
	return order


def sorted_with_order(iterable, key=None, reverse=False, inplace=False):
	assert not inplace or hasattr(iterable, '__setitem__')
	if not inplace:
		iterable = list(iterable)
	_order = order(iterable, key, reverse)
	iterable[:] = sort_by_order(iterable, _order)
	return _order, iterable


def sort_by_order(sequence, order):
	assert all(map(len(sequence).__gt__, order))
	return map(sequence.__getitem__, order)
