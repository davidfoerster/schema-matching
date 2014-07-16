from __future__ import absolute_import, division
from .probability import BaseProbabilityCollector
from .lettercount import ItemLetterCountCollector
from .letterfrequency import LetterFrequencyCollector


class LetterProbablilityCollector(BaseProbabilityCollector):

  result_dependencies = (ItemLetterCountCollector, LetterFrequencyCollector)
