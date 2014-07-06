from collector import ItemCollector


class ItemSumCollector(ItemCollector):

  def __init__(self, previous_collector_set = None):
    ItemCollector.__init__(self, previous_collector_set)
    self.sum = 0


  def collect(self, item, collector_set = None):
    self.sum += item


  def get_result(self, collector_set = None):
    return self.sum
