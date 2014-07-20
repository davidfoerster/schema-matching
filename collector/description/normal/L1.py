from collector.weight import WeightDict, normalize_exp
from collector import columntype
from collector.itemaverage import ItemAverageCollector
from collector.letteraverage import ItemLetterAverageCollector
from collector.variance import ItemVariationCoefficientCollector
from collector.lettervariance import LetterVariationCoefficient
from collector.itemprobability import ItemProbabilityCollector
from collector.letterprobability import LetterProbablilityCollector



descriptions = (
  columntype.ColumnTypeItemCollector,

  columntype.factory(
    ItemLetterAverageCollector, ItemAverageCollector),
  columntype.factory(
    LetterVariationCoefficient, ItemVariationCoefficientCollector),
  columntype.factory(
    LetterProbablilityCollector, ItemProbabilityCollector)
)


# Normalised distances and L1-normalised (Manhattan norm) collector sets
weights = WeightDict(normalize_exp, tags={'normalized'})
