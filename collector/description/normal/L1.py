from __future__ import absolute_import
from ...weight import WeightDict, normalize_exp
from ... import columntype
from ...itemaverage import ItemAverageCollector
from ...letteraverage import ItemLetterAverageCollector
from ...variance import ItemVariationCoefficientCollector
from ...lettervariance import LetterVariationCoefficient
from ...itemprobability import ItemProbabilityCollector
from ...letterprobability import LetterProbablilityCollector



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
