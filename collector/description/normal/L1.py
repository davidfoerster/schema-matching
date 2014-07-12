from __future__ import absolute_import
from ...weight import WeightDict, normalize_exp
from ...columntype import factory as columntype_factory
from ...itemaverage import ItemAverageCollector
from ...letteraverage import ItemLetterAverageCollector
from ...variance import ItemVariationCoefficientCollector
from ...lettervariance import LetterVariationCoefficient
from ...relativeletterfrequency import ItemLetterRelativeFrequencyCollector



phase_description = (
  (
    columntype_factory(
      ItemLetterAverageCollector, ItemAverageCollector),
  ),
  (
    columntype_factory(
      LetterVariationCoefficient, ItemVariationCoefficientCollector),
    columntype_factory(
      ItemLetterRelativeFrequencyCollector, None)
  )
)


# Normalised distances and L1-normalised (Manhattan norm) collector sets
collector_weights = WeightDict(normalize_exp)
