from collector.itemaverage import ItemAverageCollector
from collector.letteraverage import ItemLetterAverageCollector
from collector.variance import ItemVariationCoefficientCollector
from collector.lettervariance import LetterStandardDeviationCollector
from collector.relativeletterfrequency import ItemLetterRelativeFrequencyCollector


phase_description = (
  (collector.columntype.factory(
    ItemLetterAverageCollector, ItemAverageCollector),
  ),
  (collector.columntype.factory(
    LetterStandardDeviationCollector, ItemVariationCoefficientCollector),
  collector.columntype.factory(
    ItemLetterRelativeFrequencyCollector, None)
  )
)


collector_weights = {

}
