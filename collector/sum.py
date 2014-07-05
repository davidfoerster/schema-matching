from collector import ItemCollector


class ItemSumCollector(ItemCollector):

  def __init__(self, numeric_type):
    self.sum = 0


  def collect(self, item, collector_set = None):
    self.sum += item


  def get_result(self, collector_set = None):
    return self.sum
