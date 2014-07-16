from __future__ import absolute_import
import math, utilities.operator
from ...weight import WeightDict, normalize_exp
from .L1 import descriptions


# Normalised distances and L2-normalised (Euclidean norm) collector sets
weights = \
  WeightDict(normalize_exp, (utilities.operator.square, math.sqrt),
    tags=('normalized'))
