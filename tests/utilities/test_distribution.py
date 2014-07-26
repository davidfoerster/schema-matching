import unittest, copy
from utilities.distribution import UniformBinDistributionTable



class UniformBinDistributionTableDistanceTestCase(unittest.TestCase):

  def setUp(self):
    self.data1 = (1, 0, 5, 1, 3)
    self.dist1 = UniformBinDistributionTable(
      0, len(self.data1), None, None, self.data1)
    assert len(self.dist1) == len(self.data1)

    self.data2 = (2, 1, 0, 4, 3, 2, 1, 0, 5)
    lower2 = 0.8
    step2 = 0.4
    self.dist2 = UniformBinDistributionTable(
      lower2, lower2 + step2 * len(self.data2), len(self.data2), None, self.data2)
    assert len(self.dist2) == len(self.data2)
    assert abs(self.dist2.step - step2) < 1e-7
    self.dist2.step = step2


  def __do_test(self, a, b, expected):
    self.assertAlmostEqual(a.distance_to(b), expected)


  def test_to_self(self):
    self.__do_test(self.dist1, self.dist1, 0)


  def test_isomorph(self):
    dist3 = copy.copy(self.dist1)
    dist3.data = list(map((1).__add__, self.dist1.data))
    self.__do_test(self.dist1, dist3, len(self.dist1))


  def test_disjoint1(self):
    dist3 = copy.copy(self.dist1)
    dist3.lower = self.dist1.upper
    dist3.upper = dist3.lower + (self.dist1.upper - self.dist1.lower)
    self.__do_test(self.dist1, dist3, 2 * sum(self.data1))


  def test_disjoint2(self):
    dist3 = copy.copy(self.dist1)
    dist3.upper = self.dist1.lower
    dist3.lower = -self.dist1.upper
    self.__do_test(self.dist1, dist3, 2 * sum(self.data1))


  def test_intersecting1(self):
    dist3 = copy.copy(self.dist1)
    dist3.lower += 2
    dist3.upper += 2
    # 1: 1, 0, 5, 1, 3
    # 2:       1, 0, 5, 1, 3
    self.__do_test(self.dist1, dist3, 1 + 0 + 4 + 1 + 2 + 1 + 3)


  def test_intersecting2(self):
    dist3 = copy.copy(self.dist1)
    dist3.lower -= 1
    dist3.upper -= 1
    # 1:    1, 0, 5, 1, 3
    # 2: 1, 0, 5, 1, 3
    self.__do_test(self.dist1, dist3, 1 + 1 + 5 + 4 + 2 + 3)


  def test_contained(self):
    dist3 = copy.copy(self.dist1)
    dist3.lower += 1
    dist3.step /= 2
    dist3.upper = dist3.lower + len(dist3) * dist3.step
    self.__do_test(self.dist1, dist3, 12)


  def test_asynchronous_bins1(self):
    dist3 = copy.copy(self.dist1)
    dist3.lower += 0.5
    dist3.upper += 0.5
    # 1:            1,                          0,                         5,                           1,                          3
    # 2:                          1,                          0,                          5,                          1,                          3
    expected = .5*1 + (.5*1-.5*1) + (.5*1-.5*0) + (.5*0-.5*0) + (.5*5-.5*0) + (.5*5-.5*5) + (.5*5-.5*1) + (.5*1-.5*1) + (.5*3-.5*1) + (.5*3-.5*3) + .5*3
    self.__do_test(self.dist1, dist3, expected)


  def test_asynchronous_bins2(self):
    dist3 = copy.copy(self.dist1)
    dist3.lower += 0.4
    dist3.upper += 0.4
    self.__do_test(self.dist1, dist3, 6.4)


  def test_asynchronous_steps(self):
    self.__do_test(self.dist1, self.dist2, 14)



if __name__ == '__main__':
  unittest.main()
