from __future__  import absolute_import
from collections import defaultdict
from math import fsum, fabs


class ProbabilityDistribution(defaultdict):
  """"Holds a probability distribution and can compute the distance to other dists"""

  def __init__(self, *args):
    defaultdict.__init__(self, int, *args)


  def get(self, k, d = 0):
    return defaultdict.get(self, k, d)


  def distance_to(self, compare_to):
    return fsum((fabs(p - compare_to[bin]) for bin, p in self.iteritems())) + \
      fsum(p for bin, p in compare_to.iteritems() if bin not in self)
