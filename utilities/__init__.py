from __future__ import absolute_import
import itertools


infinity = float('inf')


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
  return all(itertools.imap(set.__contains__, iterable))


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
  return min(*xrange(len(args)), **kwargs)
