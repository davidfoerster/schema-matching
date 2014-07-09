from __future__  import absolute_import
from collections import defaultdict


class ProbabilityDistribution(defaultdict):
  """"Holds a probability distribution and can compute the distance to other dists"""

  def __init__(self, *args):
    defaultdict.__init__(self, int, *args)


  def get(self, k, d = 0):
    return defaultdict.get(self, k, d)


  def distance_to(self, compare_to):
    return sum(
      (abs(self.get(bin) - compare_to.get(bin))
        for bin in self.viewkeys() | compare_to.viewkeys()),
      0)
