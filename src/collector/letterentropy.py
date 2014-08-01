from math import fsum, log
from .base import ItemCollector
from .letterprobability import LetterProbablilityCollector



NORMALIZED = 'normalized'


class LetterEntropyCollector(ItemCollector):

  result_dependencies = (LetterProbablilityCollector,)


  def __init__(self, collector_set=None, base=2):
    super().__init__(collector_set)
    self.base = base


  def get_result(self, collector_set):
    dist = collector_set[LetterProbablilityCollector].get_result(collector_set)
    base = len(dist) if self.base is NORMALIZED else self.base
    return -fsum(map(self.__event_entropy, filter(None, dist.values()))) / log(base)


  @staticmethod
  def __event_entropy(p):
    assert 0.0 < p <= 1.0
    return p * log(p)



class NormalizedLetterEntropyCollector(LetterEntropyCollector):

  def __init__(self, collector_set=None):
    super().__init__(collector_set, NORMALIZED)
