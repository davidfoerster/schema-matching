from __future__ import absolute_import
import itertools


if __debug__:
  from __builtin__ import (map, filter)
  def filterfalse(function, iterable): return list(itertools.ifilterfalse(function, iterable))

else:
  from itertools import imap as map
  from itertools import ifilter as filter
  from itertools import ifilterfalse as filterfalse


def each(function, iterable):
  for item in iterable:
    function(item)


def each_unpack(function, iterable):
  for item in iterable:
    function(*item)


def __slice_to_tuple(slice):
  return (slice.start, slice.stop, slice.step)


def islice(iterable, *args):
  if not args:
    args = (None,)
  elif isinstance(args[0], slice):
    assert len(args) == 1
    args = __slice_to_tuple(args[0])
  return itertools.islice(iterable, *args)


def map_inplace(function, list, depth=0, slice=None):
  if depth <= 0:
    if slice is None:
      list[:] = itertools.imap(function, list)
    else:
      list[slice] = itertools.imap(function,
        itertools.islice(list, __slice_to_tuple(slice)))
  else:
    for item in list:
      map_inplace(function, item, depth - 1, slice)
  return list


def count_if(function, iterable):
  count = 0
  for item in iterable:
    if function(item):
      count += 1
  return count


def teemap(iterable, *functions):
  return map(lambda item: [item if f is None else f(item) for f in functions], iterable)
