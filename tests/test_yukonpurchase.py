import unittest
from tools.yukonpurchase import WhipsawWords,PurchaseError,purchase_selected_whipsaw,whipsaw_option_visible


class PurchaseTests(unittest.TestCase):
    def test_live_selected_eight_dollar_purchase(self):
        result=purchase_selected_whipsaw(WhipsawWords(850,0,0,4,0,0))
        self.assertEqual(result.state,WhipsawWords(842,0,1,4,17,0))
        self.assertTrue(result.action_success)
        self.assertFalse(whipsaw_option_visible(result.state.whipsaw_word))

    def test_original_bank_fallback_and_refusal(self):
        self.assertEqual(purchase_selected_whipsaw(WhipsawWords(3,8,0,4,0,0)).state,
                         WhipsawWords(0,3,1,4,17,0))
        before=WhipsawWords(7,0,0,4,0,0)
        result=purchase_selected_whipsaw(before)
        self.assertEqual((result.state,result.action_success,result.refusal_tree_id),(before,False,600))

    def test_signed_wrapping_affordability_guard(self):
        result=purchase_selected_whipsaw(WhipsawWords(32767,1,0,4,0,0))
        self.assertFalse(result.action_success)
        self.assertEqual(result.refusal_tree_id,600)

    def test_gate_suppresses_mutation_but_success_return_is_preserved(self):
        before=WhipsawWords(850,0,0,4,123,1)
        result=purchase_selected_whipsaw(before)
        self.assertEqual((result.state,result.action_success),(before,True))

    def test_unsupported_operations_and_context_fail(self):
        for state in (WhipsawWords(850,0,1,4,0,0),WhipsawWords(850,0,0,1,0,0)):
            with self.assertRaises(PurchaseError):purchase_selected_whipsaw(state)
        with self.assertRaises(PurchaseError):purchase_selected_whipsaw(WhipsawWords(850,0,0,4,0,0),action=(220,109,9,0))
        with self.assertRaises(PurchaseError):whipsaw_option_visible(-1)
