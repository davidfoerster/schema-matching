from collector import ItemCollector


class ItemLetterCountCollector(ItemCollector):

  def __init__(self):
    self.letter_count = 0


  def collect(self, item, collector_set = None):
    self.letter_count += len(item)


  def get_result(self, collector_set = None):
    return self.letter_count
