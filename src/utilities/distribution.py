import numbers, array, itertools, operator, math
from collections import defaultdict
from math import fsum, fabs
from utilities.string import join, format_char



default_number_format = '.4g'



class DistributionTable(object):

  def count(self):
    return NotImplemented


  def __truediv__(self, divisor):
    return NotImplemented


  def __str__(self):
    return self.__format__(default_number_format)


  def normalize(self, count=None):
    if count is None:
      count = self.count()
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
    return fsum((fabs(p - compare_to[bin]) for bin, p in self.items())) + \
      fsum(p for bin, p in compare_to.items() if bin not in self)


  def count(self):
    return sum(self.values())


  def __truediv__(self, divisor):
    """
    :param divisor: numbers.Real
    :return: SparseDistributionTable
    """
    divisor = float(divisor)
    return SparseDistributionTable(float,
      ((k, v / divisor) for k, v in self.items()))


  def __format__(self, number_format_spec=''):
    return join('(',
      ', '.join((
        '{}: {:{}}'.format(format_char(event), frequency, number_format_spec)
        for event, frequency in self.items())),
      ')')



class UniformBinDistributionTable(DistributionTable):

  def __init__(self, start, stop, bincount=None, datatype=None, initializer=None):
    super().__init__()

    assert stop > start
    if bincount is None:
      bincount = int(math.ceil(stop - start))
    assert isinstance(bincount, numbers.Integral) and bincount >= 1
    self.lower = start
    self.upper = stop
    self.step = (stop - start) / bincount

    if initializer is None:
      initializer = itertools.repeat(0, bincount)
    self.data = list(initializer) if datatype is None else array.array(datatype, initializer)
    excess = len(self.data) - bincount
    if excess > 0:
      del self.data[bincount:]
    elif excess < 0:
      self.data.extend(itertools.repeat(0, -excess))


  def datatype(self):
    return self.data.typecode if isinstance(self.data, array.array) else None


  def bincount(self):
    return len(self.data) + 1


  def getbinlimits(self, binidx):
    return binidx * self.step + self.lower, (binidx + 1) * self.step + self.lower


  def getbinidx(self, key):
    if key <= self.lower:
      return 0
    if key >= self.upper:
      return len(self.data) - 1
    else:
      return int((key - self.lower) / self.step)


  def __getitem__(self, key):
    return self.data[self.getbinidx(key)]


  def __setitem__(self, key, value):
    self.data[self.getbinidx(key)] = value


  def increase(self, key, value):
    self.data[self.getbinidx(key)] += value


  def __len__(self):
    return len(self.data)


  def __iter__(self):
    return iter(self.data)


  def count(self):
    return sum(self)


  def __truediv__(self, divisor):
    return UniformBinDistributionTable(self.lower, self.upper, self.bincount(), 'd',
      map(float(divisor).__rtruediv__, self.data))


  def distance_to(self, compare_to):
    if isinstance(compare_to, UniformBinDistributionTable):
      if self.lower == compare_to.lower and self.upper == compare_to.upper and self.step == compare_to.step:
        assert self.bincount() == compare_to.bincount()
        compare_to = compare_to.data
      else:
        # TODO
        #return NotImplemented
        return float('inf')

    assert not hasattr(compare_to, '__len__') or len(self.data) == len(compare_to)
    return fsum(map(fabs, map(operator.sub, self.data, compare_to)))


  def __format__(self, number_format_spec=''):
    return join('(',
      ', '.join((
        '{2:{0}}-{3:{0}}: {1:{0}}'.format(
          number_format_spec, frequency, *self.getbinlimits(bin_idx))
        for bin_idx, frequency in enumerate(self))),
      ')')


  @staticmethod
  def for_count(count, lower, upper, *args):
    """ uses Sturge's rule: ceil(1 + log2(count)) """
    return UniformBinDistributionTable(
      lower, upper, _sturges_rule(count), *args)


  @staticmethod
  def for_variance(count, lower, upper, variance, *args):
    """ uses Scott's rule, limited by the double of Sturge's """
    h = int(math.ceil(3.49 * math.sqrt(variance) / _cubicroot(count)))
    return UniformBinDistributionTable(
      lower, upper, min(h, 2 * _sturges_rule(count)), *args)


  @staticmethod
  def for_quartiles(count, lower, upper, q1, q3, *args):
    """ uses Freedman's and Diaconis' rule """
    h = int(math.ceil(2.0 * (q3 - q1) / _cubicroot(count)))
    return UniformBinDistributionTable(
      lower, upper, min(h, 2 * _sturges_rule(count)), *args)



def _sturges_rule(n):
  return (n - 1).bit_length() + 1


def _cubicroot(x):
  return x ** (1. / 3.)
