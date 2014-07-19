import utilities
import utilities.iterator as uiterator
import utilities.operator as uoperator
from math import expm1, fsum



class WeightDict(dict):

  class WeightFunctor(object):

    __cache = dict()

    def __new__(cls, weight):
      return \
        weight if type(weight) is cls else \
          cls.__cache.get(weight) or object.__new__(cls)

    def __init__(self, weight):
      object.__init__(self)
      if callable(weight):
        self.weightfn = weight
        self.coefficient = 1
      else:
        self.weightfn = weight.__mul__
        self.coefficient = weight
      self.__cache.setdefault(weight, self)

    def __call__(self, x):
      return self.weightfn(x)


  def __new__(cls, *args, **kwargs):
    return dict.__new__(cls)


  def __init__(self, default=uoperator.identity, sum=(abs, uoperator.identity), *args, **kwargs):
    dict.__init__(self)
    self.default = WeightDict.WeightFunctor(default)
    self.sum_data = sum
    self.tags = kwargs.pop('tags', frozenset())
    uiterator.stareach(self.__setitem__, args)
    uiterator.stareach(self.__setitem__, kwargs.items())


  def __missing__(self, key):
    return self.default


  def __setitem__(self, key, value):
    dict.__setitem__(self, key, WeightDict.WeightFunctor(value))


  def setdefault(self, k, d=uoperator.identity):
    dict.setdefault(self, k, WeightDict(d))


  def sum(self, iterable):
    return self.sum_data[1](fsum(map(self.sum_data[0], iterable)))



def normalize_exp(x):
  """
  Returns
     -(exp(-x) - 1)
   = -(exp(-x) - 1)
   = 1 - exp(-x)

  This gives us a nicely normalised distance measure that penalises large
  values subproportionally.
  """
  return -expm1(-x)
