import unittest
from tools.yukoncalendar import DateWords, CalendarError, advance_one_original_day, enter_selected_seattle_scene


class CalendarTests(unittest.TestCase):
    def test_selected_august_transition(self):
        self.assertEqual(advance_one_original_day(DateWords(23, 8, 0, 0, 0)),
                         DateWords(24, 8, 1, 0, 0))

    def test_original_february_has_fixed_twenty_eight_days(self):
        self.assertEqual(advance_one_original_day(DateWords(28, 2, 200, 6, 0)),
                         DateWords(1, 3, 201, 7, 0))

    def test_december_and_word_wrap(self):
        self.assertEqual(advance_one_original_day(DateWords(31, 12, 65535, 65535, 0)),
                         DateWords(1, 1, 0, 0, 0))

    def test_nonzero_gate_suppresses_all_date_words(self):
        before = DateWords(31, 12, 65535, 65535, 1)
        self.assertEqual(advance_one_original_day(before), before)

    def test_unsupported_invalid_dates_fail(self):
        for day, month in ((0, 8), (29, 2), (31, 4), (23, 0), (23, 13)):
            with self.assertRaises(CalendarError):
                DateWords(day, month, 0, 0, 0)

    def test_selected_first_visit_and_revisit(self):
        before=DateWords(23,8,0,0,0)
        self.assertEqual(enter_selected_seattle_scene(before,1000,0),(DateWords(24,8,1,0,0),1))
        self.assertEqual(enter_selected_seattle_scene(before,1000,65535),(before,1))
        self.assertEqual(enter_selected_seattle_scene(before,4000,0),(before,1))
        for merchant in (2000,3000):self.assertEqual(enter_selected_seattle_scene(before,merchant,0),(before,1))
        blocked=DateWords(23,8,0,0,1)
        self.assertEqual(enter_selected_seattle_scene(blocked,1000,0),(blocked,0))
        with self.assertRaises(CalendarError):enter_selected_seattle_scene(before,5000,0)
