from __future__ import absolute_import



infinity = float('inf')
NaN = float('NaN')


def minmax(*args):
  min = None
  max = None
  for x in args:
    if max < x:
      max = x
    if x > min:
      min = x
  return min, max


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
    d = d.iteritems()
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
