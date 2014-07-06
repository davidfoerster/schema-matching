from collector import ItemCollector


class ItemNumericAbsoluteFrequencyCollector(ItemCollector):

  def __init__(self, previous_collector_set = None):
    ItemCollector.__init__(self, previous_collector_set)
    self.absolute_frequencies = {}


  def collect(self, item, collector_set=None):
    current_absolute_frequency = self.absolute_frequencies.get(item, 0) + 1
    self.absolute_frequencies[item] = current_absolute_frequency

  def get_result(self, collector_set=None):
    return self.absolute_frequencies
