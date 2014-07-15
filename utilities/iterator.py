from __future__ import absolute_import
import __builtin__, itertools


if __debug__:
  from __builtin__ import (map, filter)
  def filterfalse(function, iterable): return list(itertools.ifilterfalse(function, iterable))

else:
  from itertools import imap as map
  from itertools import ifilter as filter
  from itertools import ifilterfalse as filterfalse


def each(function, *iterables):
  if not iterables:
    return
  elif len(iterables) == 1:
    for args in iterables[0]:
      function(args)
  else:
    stareach(function, itertools.izip(*iterables))


def stareach(function, iterable):
  for args in iterable:
    function(*args)


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
      list[:] = itertools.imap(function, list)
    else:
      list[slice] = itertools.imap(function,
        itertools.islice(list, slice.start, slice.stop, slice.step))
  else:
    for item in list:
      map_inplace(function, item, depth - 1, slice)
  return list


def countif(function, *iterables):
  return sum(itertools.imap(bool, itertools.starmap(function, *iterables)))


def teemap(iterable, *functions):
  return map(lambda item: [item if f is None else f(item) for f in functions], iterable)
