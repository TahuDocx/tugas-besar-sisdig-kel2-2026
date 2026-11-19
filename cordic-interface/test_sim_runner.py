"""Tests for sim_runner: GUI form values -> cordic-sim-py report text."""

import unittest

from sim_runner import (FUNCS, cordic, errorSweep, formatDuration, fpgaCycles, fpgaTime,
                        minIterations, simulate, simulateTimed)


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


class ErrorSweepTest(unittest.TestCase):
    def _expected(self, func, t, n_max, **kw):
        out = []
        for n in range(1, n_max + 1):
            r = cordic.compute(func, t, n, **kw)
            out.append([n, abs(r.value - r.expected)])
        return out

    def test_fixed_points_match_compute(self):
        self.assertEqual(errorSweep("cosh", "0.5", 8, True, 14, 16),
                         self._expected("cosh", 0.5, 8, frac=14, width=16))

    def test_float_points_match_compute(self):
        self.assertEqual(errorSweep("ln", " 2 ", 12, False, 99, 1),
                         self._expected("ln", 2.0, 12))

    def test_float_error_shrinks_with_iterations(self):
        pts = errorSweep("exp", "0.5", 24, False, 14, 16)
        self.assertLess(pts[-1][1], pts[1][1] * 1e-4)

    def test_one_point_per_iteration_count(self):
        pts = errorSweep("sinh", "0.3", 5, True, 14, 16)
        self.assertEqual([p[0] for p in pts], [1, 2, 3, 4, 5])

    def test_undefined_expected_gives_no_points(self):
        self.assertEqual(errorSweep("atanh", "1.5", 8, False, 14, 16), [])

    def test_propagates_errors(self):
        with self.assertRaises(ValueError):
            errorSweep("cosh", "abc", 8, True, 14, 16)
        with self.assertRaises(ValueError):
            errorSweep("cosh", "0.5", 0, True, 14, 16)
        with self.assertRaises(ValueError):
            errorSweep("cosh", "0.5", 8, True, 16, 16)


class MinIterationsTest(unittest.TestCase):
    def test_monotonic_first_under_tol(self):
        pts = [[1, 0.5], [2, 0.1], [3, 0.01], [4, 0.001]]
        self.assertEqual(minIterations(pts, 0.01), 3)

    def test_lucky_dip_is_skipped(self):
        pts = [[1, 0.5], [2, 0.001], [3, 0.2], [4, 0.005], [5, 0.004]]
        self.assertEqual(minIterations(pts, 0.01), 4)

    def test_equal_to_tol_counts(self):
        self.assertEqual(minIterations([[1, 0.2], [2, 0.01]], 0.01), 2)

    def test_last_point_above_tol_gives_zero(self):
        self.assertEqual(minIterations([[1, 0.001], [2, 0.5]], 0.01), 0)

    def test_empty_gives_zero(self):
        self.assertEqual(minIterations([], 0.01), 0)

    def test_all_under_tol_gives_first_n(self):
        self.assertEqual(minIterations([[1, 0.0], [2, 0.0]], 0.01), 1)

    def test_bad_tol(self):
        for tol in (0.0, -1e-3, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                minIterations([[1, 0.1]], tol)


if __name__ == "__main__":
    unittest.main()
