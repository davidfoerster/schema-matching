__all__ = ('memberfn', 'composefn', 'partialfn', 'reduce')

from .operator import identity
from operator import methodcaller
from itertools import starmap
from functools import reduce, partial as partialfn
import inspect



class memberfn:
	"""Binds arguments for instance(-like) method calls.

	Instances of this class are callable and pass their single positional
	argument as the first positional argument to the wrapped function followed by
	the other arguments given during instantiation."""

	__slots__ = ('func', 'args', 'kwargs')


	def __new__(cls, func, *args, **kwargs):
		if not callable(func):
			return methodcaller(func, *args, **kwargs)
		if not args and not kwargs:
			return func
		return super().__new__(cls)


	def __init__(self, func, *args, **kwargs):
		self.func = func
		self.args = args
		self.kwargs = kwargs


	def __call__(self, obj):
		return self.func(obj, *self.args, **self.kwargs)


	def __repr__(self):
		return '{:s}({:s})'.format(
			type(self).__qualname__,
			', '.join((
				func_repr(self.func), *map(repr, self.args),
				*starmap('{:s}={!r}'.format, self.kwargs.items()))))


class composefn:
	"""A function object that concatenates the passed functions from left to
	right.
	"""

	__slots__ = ('funcs',)


	def __new__(cls, *funcs):
		assert all(map(callable, funcs))
		if len(funcs) > 1:
			return super().__new__(cls)
		if funcs:
			return funcs[0]
		return identity


	def __init__(self, *funcs):
		self.funcs = funcs


	def __call__(self, *args, **kwargs):
		funcs = iter(self.funcs)
		args = next(funcs, identity)(*args, **kwargs)
		del kwargs
		for f in funcs:
			args = f(args)
		return args


	def __repr__(self):
		return '{:s}({:s})'.format(
			type(self).__qualname__, ', '.join(tuple(map(func_repr, self.funcs))))


def func_repr(func):
	if isinstance(func, type) or inspect.isroutine(func):
		func_module = getattr(
			getattr(func, '__objclass__', func), '__module__', None)
		if func_module is not None:
			if func_module == 'builtins':
				return func.__qualname__
			return '.'.join((func_module, func.__qualname__))
	return repr(func)
