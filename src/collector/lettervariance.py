from math import sqrt
from utilities.operator import square
from .base import ItemCollector
from .lettercount import ItemLetterCountCollector
from .letteraverage import ItemLetterAverageCollector



class LetterVarianceCollector(ItemCollector):

  pre_dependencies = (ItemLetterAverageCollector,)

  result_dependencies = (ItemLetterCountCollector,)


  def __init__(self, previous_collector_set):
    super().__init__(previous_collector_set)
    self.sum_of_squares = 0
    self.letter_average = \
      previous_collector_set[ItemLetterAverageCollector] \
        .get_result(previous_collector_set)


  def collect(self, item, collector_set = None):
    self.sum_of_squares += square(len(item) - self.letter_average)


  def get_result(self, collector_set):
    return self.sum_of_squares / collector_set[ItemLetterCountCollector].get_result()



class LetterStandardDeviationCollector(ItemCollector):

  result_dependencies = (LetterVarianceCollector,)

  def get_result(self, collector_set):
    return sqrt(collector_set[LetterVarianceCollector].get_result(collector_set))



class LetterVariationCoefficient(ItemCollector):

  result_dependencies = (LetterVarianceCollector,)

  def get_result(self, collector_set):
    varcoll = collector_set[LetterVarianceCollector]
    return sqrt(varcoll.get_result(collector_set)) / varcoll.letter_average
