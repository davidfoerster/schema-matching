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


class ProbabilityDistribution(collections.defaultdict):
  """"Holds a probability distribution and can compute the distance to other dists"""

  def __init__(self):
    collections.defaultdict.__init__(self, int)


  def get(self, k, d = 0):
    return dict.get(self, k, d)


  def distance_to(self, compare_to):
    key_set = self.viewkeys() | compare_to.viewkeys()

    currentEMD = 0
    lastEMD = 0
    totaldistance = 0

    for key in key_set:
      lastEMD = currentEMD
      currentEMD = (self.get(key, 0) + lastEMD) - compare_to.get(key, 0)
      totaldistance += math.fabs(currentEMD)

    return totaldistance