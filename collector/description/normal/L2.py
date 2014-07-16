from __future__ import absolute_import
import math, utilities.operator
from ...weight import WeightDict, normalize_exp
from .L1 import phase_description


# Normalised distances and L2-normalised (Euclidean norm) collector sets
collector_weights = \
  WeightDict(normalize_exp, (utilities.operator.square, math.sqrt),
    tags=('normalized'))
