import unittest

from tools.yukonseattle import State, UnsupportedOperation, accept_linda, change_money_slot_zero, linda_scene_child_eligible


class SeattleTests(unittest.TestCase):
    def state(self, cash=350, bank=0, gate=0):
        return State(cash, bank, 0, gate, 0)

    def test_linda_native_transition(self):
        actual, success = accept_linda(self.state())
        self.assertTrue(success)
        self.assertEqual(actual, State(850, 0, 4, 0, 1))

    def test_native_gate_preserves_cash_partner_but_sets_flag344(self):
        actual, success = accept_linda(self.state(gate=1))
        self.assertEqual((actual, success), (State(350, 0, 0, 1, 1), True))

    def test_native_sixty_dollar_deduction(self):
        actual, success = change_money_slot_zero(self.state(850), -60)
        self.assertEqual((actual.cash_word, actual.bank_word, success), (790, 0, True))

    def test_native_bank_fallback(self):
        actual, success = change_money_slot_zero(self.state(20, 100), -60)
        self.assertEqual((actual.cash_word, actual.bank_word, success), (0, 60, True))

    def test_native_insufficient_total_is_atomic_for_money(self):
        before = self.state(20, 30)
        self.assertEqual(change_money_slot_zero(before, -60), (before, False))

    def test_native_signed_overflow_clamp(self):
        actual, success = change_money_slot_zero(self.state(32760), 500)
        self.assertEqual((actual.cash_word, success), (0, True))

    def test_selected_linda_child_native_eligibility(self):
        for partner in (0, 1, 2, 3, 5, 32767, 32768, 65534, 65535):
            self.assertFalse(linda_scene_child_eligible(partner))
        self.assertTrue(linda_scene_child_eligible(4))
        with self.assertRaises(UnsupportedOperation):
            linda_scene_child_eligible(65536)

    def test_reject_unsupported_action_and_delta(self):
        for options in ({'opcode': 0xfa}, {'partner': 1}, {'amount': 750}):
            with self.assertRaises(UnsupportedOperation):
                accept_linda(self.state(), **options)
        with self.assertRaises(UnsupportedOperation):
            change_money_slot_zero(self.state(), 32768)
        with self.assertRaises(UnsupportedOperation):
            State(-1, 0, 0, 0, 0)


if __name__ == '__main__':
    unittest.main()
