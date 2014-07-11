from __future__ import absolute_import
import collector.itemaverage, collector.letteraverage
from ..columntype import factory as columntype_factory
from ..itemaverage import ItemAverageCollector
from ..letteraverage import ItemLetterAverageCollector
from ..variance import ItemVariationCoefficientCollector
from ..lettervariance import LetterVariationCoefficient
from ..relativeletterfrequency import ItemLetterRelativeFrequencyCollector



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

collector_weights = {
  ItemAverageCollector:  collector.itemaverage.normalize,
  ItemLetterAverageCollector: collector.letteraverage.normalize,
}
