from __future__ import absolute_import
import itertools


if __debug__:
  from __builtin__ import (map, filter)
  def filterfalse(function, iterable): return list(itertools.ifilterfalse(function, iterable))

else:
  from itertools import imap as map
  from itertools import ifilter as filter
  from itertools import ifilterfalse as filterfalse


def each(function, *iterables):
  if len(iterables) <= 1:
    for args in iterables[0]:
      function(args)
  else:
    iterables = map(iter, iterables)
    while True:
      try:
        args = map(next, iterables)
      except StopIteration:
        break
      else:
        function(*args)


def stareach(function, iterable):
  for args in iterable:
    function(*args)


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


def countif(function, *iterables):
  count = 0
  if len(iterables) <= 1:
    for args in iterables[0]:
      if function(args):
        count += 1
  else:
    iterables = map(iter, iterables)
    while True:
      try:
        args = map(next, iterables)
      except StopIteration:
        break
      else:
        if function(*args):
          count += 1
  return count


def teemap(iterable, *functions):
  return map(lambda item: [item if f is None else f(item) for f in functions], iterable)
