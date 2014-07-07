from collector import ItemCollector


class ItemLetterCountCollector(ItemCollector):

  def __init__(self, previous_collector_set = None):
    ItemCollector.__init__(self, previous_collector_set)
    self.letter_count = 0


  def collect(self, item, collector_set = None):
    assert isinstance(item, str)
    self.letter_count += len(item)


  def get_result(self, collector_set = None):
    return self.letter_count
