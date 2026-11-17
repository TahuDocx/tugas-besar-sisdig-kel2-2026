"""Tests for sim_runner: GUI form values -> cordic-sim-py report text."""

import unittest

from sim_runner import FUNCS, cordic, formatDuration, fpgaCycles, fpgaTime, simulate, simulateTimed


class SimulateTest(unittest.TestCase):
    def test_fixed_matches_cordic_report(self):
        expected = cordic.formatReport(cordic.compute("cosh", 0.5, 16, frac=14, width=16))
        self.assertEqual(simulate("cosh", "0.5", 16, True, 14, 16), expected)

    def test_float_matches_cordic_report(self):
        expected = cordic.formatReport(cordic.compute("ln", 2.0, 20))
        self.assertEqual(simulate("ln", " 2 ", 20, False, 14, 16), expected)

    def test_float_ignores_bad_frac_width(self):
        self.assertIn("format float", simulate("exp", "0.1", 8, False, 99, 1))

    def test_t_not_a_number(self):
        with self.assertRaises(ValueError):
            simulate("cosh", "abc", 16, True, 14, 16)

    def test_t_not_finite(self):
        with self.assertRaises(ValueError):
            simulate("cosh", "nan", 16, True, 14, 16)

    def test_unknown_func(self):
        with self.assertRaises(ValueError):
            simulate("tan", "0.5", 16, True, 14, 16)

    def test_n_below_one(self):
        with self.assertRaises(ValueError):
            simulate("cosh", "0.5", 0, True, 14, 16)

    def test_frac_not_below_width(self):
        with self.assertRaises(ValueError):
            simulate("cosh", "0.5", 16, True, 16, 16)

    def test_width_too_small(self):
        with self.assertRaises(ValueError):
            simulate("cosh", "0.5", 16, True, 0, 1)

    def test_funcs_reexported(self):
        self.assertEqual(FUNCS, cordic.FUNCS)


class TimingTest(unittest.TestCase):
    def test_cycles_are_load_plus_iterations(self):
        self.assertEqual(fpgaCycles(16), 17)
        self.assertEqual(fpgaCycles(1), 2)

    def test_fpga_time_at_50mhz(self):
        self.assertAlmostEqual(fpgaTime(16, 50.0), 17 / 50e6)

    def test_fpga_time_rejects_bad_clock(self):
        with self.assertRaises(ValueError):
            fpgaTime(16, 0.0)

    def test_format_ns(self):
        self.assertEqual(formatDuration(340e-9), "340 ns")

    def test_format_us(self):
        self.assertEqual(formatDuration(48.24e-6), "48.2 µs")

    def test_format_ms(self):
        self.assertEqual(formatDuration(1.25e-3), "1.25 ms")

    def test_format_s(self):
        self.assertEqual(formatDuration(2.5), "2.5 s")

    def test_format_rounds_up_into_next_unit(self):
        self.assertEqual(formatDuration(999.9e-9), "1 µs")

    def test_timed_returns_same_report_and_positive_time(self):
        report, seconds = simulateTimed("cosh", "0.5", 16, True, 14, 16)
        self.assertEqual(report, simulate("cosh", "0.5", 16, True, 14, 16))
        self.assertGreater(seconds, 0.0)

    def test_timed_propagates_errors(self):
        with self.assertRaises(ValueError):
            simulateTimed("cosh", "abc", 16, True, 14, 16)


if __name__ == "__main__":
    unittest.main()
