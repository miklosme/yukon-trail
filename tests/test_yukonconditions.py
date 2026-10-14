import unittest
from tools.yukonconditions import evaluate_seattle_condition,ConditionError

class ExplicitConditionScope(unittest.TestCase):
    def test_unsupported_kinds_and_unobserved_special_contexts_fail(self):
        state=bytes(0x386)
        for condition,index in(((99,0),17),((11,106),17),((7,1),9)):
            with self.assertRaises(ConditionError):evaluate_seattle_condition(condition,state,index,0)

    def test_projection_missing_settings_and_unbounded_index_fail(self):
        for state,index,units in((bytes(0x314),17,0),(bytes(0x386),61,0),(bytes(0x386),17,None)):
            with self.assertRaises(ConditionError):evaluate_seattle_condition((2,1),state,index,units)
