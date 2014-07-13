from __future__  import absolute_import, division
import numbers
from collections import defaultdict
from math import fsum, fabs


class DistributionTable(object):

  def count(self):
    return NotImplemented


  def __truediv__(self, divisor):
    return NotImplemented


  def normalize(self, count=None):
    if count is None:
      count = self.count()
    else:
      assert count == self.count()
    return self / count



class SparseDistributionTable(DistributionTable, defaultdict):
  """"Holds a probability distribution and can compute the distance to other dists"""

  def __init__(self, type=int, *args):
    """
    :param type: type
    :param args: *
    :return:
    """
    assert issubclass(type, numbers.Real)
    DistributionTable.__init__(self)
    defaultdict.__init__(self, type, *args)


  def distance_to(self, compare_to):
    return fsum((fabs(p - compare_to[bin]) for bin, p in self.iteritems())) + \
      fsum(p for bin, p in compare_to.iteritems() if bin not in self)


  def count(self):
    return sum(self.itervalues())


  def __truediv__(self, divisor):
    """
    :param divisor: numbers.Real
    :return: SparseDistributionTable
    """
    coerced = coerce(self.default_factory(), divisor)
    assert coerced is not None
    return SparseDistributionTable(type(coerced[0]),
      ((k, v / divisor) for k, v in self.iteritems()))
