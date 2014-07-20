import math, utilities.operator
from collector.weight import WeightDict, normalize_exp
from collector.description.normal.L1 import descriptions


# Normalised distances and L2-normalised (Euclidean norm) collector sets
weights = \
  WeightDict(normalize_exp, (utilities.operator.square, math.sqrt),
    tags=('normalized'))
