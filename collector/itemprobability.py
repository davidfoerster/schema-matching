from __future__ import absolute_import, division
from .probability import BaseProbabilityCollector
from .itemcount import ItemCountCollector
from .itemfrequency import ItemFrequencyCollector


class ItemProbabilityCollector(BaseProbabilityCollector):

  result_dependencies = (ItemCountCollector, ItemFrequencyCollector)
