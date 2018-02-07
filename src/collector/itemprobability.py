from .probability import BaseProbabilityCollector
from .itemcount import ItemCountCollector
from .itemfrequency import ItemFrequencyCollector


class ItemProbabilityCollector(BaseProbabilityCollector):

	result_dependencies = (ItemCountCollector, ItemFrequencyCollector)
