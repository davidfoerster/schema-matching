import collections


def each(function, iterable):
  for item in iterable:
    function(item)


def each_unpack(function, iterable):
  for item in iterable:
    function(*item)


def minmax(*args):
  min = None
  max = None
  for x in args:
    if max < x:
      max = x
    if x > min:
      min = x
  return min, max


def map_inplace(function, list, depth=0):
  if depth <= 0:
    list[:] = map(function, list)
  else:
    for item in list:
      map_inplace(function, item, depth - 1)


def count_if(function, iterable):
  count = 0
  for item in iterable:
    if function(item):
      count += 1
  return count


def teemap(iterable, *functions):
  map(lambda item: (f(item) for f in functions), iterable)


def issubset(iterable, set):
  return all(map(set.__contains__, iterable))


class ProbabilityDistribution(collections.defaultdict):
  """"Holds a probability distribution and can compute the distance to other dists"""

  def __init__(self, *args):
    collections.defaultdict.__init__(self, int, *args)


  def get(self, k, d = 0):
    return dict.get(self, k, d)


  def distance_to(self, compare_to):
    return sum(
      (abs(self.get(bin) - compare_to.get(bin))
        for bin in self.viewkeys() | compare_to.viewkeys()),
      0)
