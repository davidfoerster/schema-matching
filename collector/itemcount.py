from collector import ItemCollector


class ItemCountCollector(ItemCollector):

  def __init__(self, previous_collector_set = None):
    ItemCollector.__init__(self, previous_collector_set)
    self.count = 0


  def collect(self, item, collector_set = None):
    self.count += 1


  def get_result(self, collector_set = None):
    return self.count
