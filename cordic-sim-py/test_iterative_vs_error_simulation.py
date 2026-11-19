"""Tests for iterative_vs_error_simulation: worst-case error sweep and best-n pickers."""

import math
import unittest

import cordic
from iterative_vs_error_simulation import (LE_OVERHEAD, atCost, bestByDelta, bestByProduct,
                                           cheapestN, errorDeltas, errorTable, estimateLEs,
                                           maxWidthForLEs,
                                           paretoFront, pickFormat, tGrid, uartSeconds,
                                           widthSummary, worstError)


class TGridTest(unittest.TestCase):
    def test_rotation_funcs_span_theta_max(self):
        tm = cordic.thetaMax(64)
        for func in ("cosh", "sinh", "exp"):
            ts = tGrid(func, 11)
            self.assertEqual(len(ts), 11)
            self.assertAlmostEqual(ts[0], -tm)
            self.assertAlmostEqual(ts[-1], tm)

    def test_vectoring_funcs_stay_in_range(self):
        for func in ("atanh", "ln", "sqrt"):
            ts = tGrid(func, 21)
            self.assertEqual(len(ts), 21)
            for t in ts:
                self.assertTrue(cordic.compute(func, t, 64).in_range, (func, t))

    def test_points_ascending(self):
        ts = tGrid("ln", 9)
        self.assertEqual(ts, sorted(ts))

    def test_bad_args(self):
        with self.assertRaises(ValueError):
            tGrid("cosh", 1)
        with self.assertRaises(ValueError):
            tGrid("tan", 11)


class WorstErrorTest(unittest.TestCase):
    def test_is_max_abs_error_over_ts(self):
        ts = [-0.9, -0.2, 0.0, 0.4, 1.0]
        expected = max(abs(r.value - r.expected) for r in
                       (cordic.compute("cosh", t, 10, frac=12, width=14) for t in ts))
        self.assertEqual(worstError("cosh", 10, 12, 14, ts), expected)

    def test_empty_ts(self):
        with self.assertRaises(ValueError):
            worstError("cosh", 10, 12, 14, [])


class ErrorTableTest(unittest.TestCase):
    def test_rows_per_frac_and_width_is_frac_plus_int_bits(self):
        ts = [-0.5, 0.25, 0.75]
        table = errorTable("sinh", [8, 10], 5, 2, ts)
        self.assertEqual(sorted(table), [8, 10])
        for frac, errs in table.items():
            self.assertEqual(len(errs), 5)
            for n in range(1, 6):
                self.assertEqual(errs[n - 1], worstError("sinh", n, frac, frac + 2, ts))


class BestByProductTest(unittest.TestCase):
    def test_argmin_of_n_times_error(self):
        # products 0.5, 0.2, 0.15, 0.2
        self.assertEqual(bestByProduct([0.5, 0.1, 0.05, 0.05]), 3)

    def test_tie_gives_smallest_n(self):
        # products 0.4, 0.4, 0.6
        self.assertEqual(bestByProduct([0.4, 0.2, 0.2]), 1)

    def test_empty(self):
        with self.assertRaises(ValueError):
            bestByProduct([])


class ErrorDeltasTest(unittest.TestCase):
    def test_previous_minus_current(self):
        d = errorDeltas([1.0, 0.25, 0.5])
        self.assertEqual(d, [0.75, -0.25])

    def test_short_input(self):
        self.assertEqual(errorDeltas([1.0]), [])


class BestByDeltaTest(unittest.TestCase):
    def test_no_later_gain_of_one_lsb(self):
        # n=2 -> later best 0.19 gains 0.31; n=3 -> later gains 0.01 and -0.10
        self.assertEqual(bestByDelta([1.0, 0.5, 0.2, 0.19, 0.30], 0.05), 3)

    def test_plateau_then_big_drop_is_not_a_stop(self):
        self.assertEqual(bestByDelta([1.0, 0.5, 0.49, 0.1], 0.05), 4)

    def test_gain_of_exactly_one_lsb_still_counts(self):
        # binary fractions so the gain is exactly 1 LSB (0.25 - 0.20 is not 0.05 in float)
        self.assertEqual(bestByDelta([0.5, 0.25, 0.1875], 0.0625), 3)

    def test_later_recovery_after_blowup_does_not_move_pick(self):
        # n=1 is beaten by 0.2 (>= lsb); n=2 is never beaten; 5.0 -> 4.0 later (overflow
        # recovering) must not matter
        self.assertEqual(bestByDelta([0.3, 0.1, 0.2, 5.0, 4.0], 0.1), 2)

    def test_flat_gives_first_n(self):
        self.assertEqual(bestByDelta([0.1, 0.1, 0.1], 0.05), 1)

    def test_bad_args(self):
        with self.assertRaises(ValueError):
            bestByDelta([0.1], 0.0)
        with self.assertRaises(ValueError):
            bestByDelta([], 0.05)


class CheapestNTest(unittest.TestCase):
    def test_first_n_at_or_under_tol(self):
        self.assertEqual(cheapestN([0.5, 0.25, 0.125, 0.25], 0.25), 2)

    def test_none_under_tol_gives_zero(self):
        self.assertEqual(cheapestN([0.5, 0.25], 0.125), 0)

    def test_bad_tol(self):
        for tol in (0.0, -1.0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                cheapestN([0.5], tol)


class AtCostTest(unittest.TestCase):
    def test_width_times_cycles(self):
        # width 16 = 14 + 2, cycles 17 = 1 load + 16 iterations
        self.assertEqual(atCost(14, 16, 2), 16 * 17)


class PickFormatTest(unittest.TestCase):
    TABLE = {
        4: [0.5, 0.25, 0.25, 0.25],       # never reaches 0.125
        6: [0.5, 0.25, 0.125, 0.0625],    # 0.125 at n=3 -> cost 8 * 4 = 32
        8: [0.5, 0.125, 0.0625, 0.0625],  # 0.125 at n=2 -> cost 10 * 3 = 30
    }

    def test_cheapest_at_cost_wins(self):
        self.assertEqual(pickFormat(self.TABLE, 2, 0.125), (8, 2))

    def test_tie_prefers_narrower_width(self):
        table = {6: [0.5, 0.5, 0.5, 0.5, 0.125],   # n=5 -> 8 * 6 = 48
                 10: [0.5, 0.5, 0.125]}            # n=3 -> 12 * 4 = 48
        self.assertEqual(pickFormat(table, 2, 0.125), (6, 5))

    def test_unreachable_gives_none(self):
        self.assertIsNone(pickFormat(self.TABLE, 2, 0.01))


class ParetoFrontTest(unittest.TestCase):
    def test_keeps_only_non_dominated(self):
        pts = [(10, 0.5), (20, 0.25), (20, 0.4), (30, 0.3), (40, 0.1), (5, 0.9)]
        self.assertEqual(paretoFront(pts), [(5, 0.9), (10, 0.5), (20, 0.25), (40, 0.1)])

    def test_equal_cost_keeps_lower_error_only(self):
        self.assertEqual(paretoFront([(10, 0.5), (10, 0.3)]), [(10, 0.3)])

    def test_extra_fields_are_kept(self):
        self.assertEqual(paretoFront([(10, 0.5, "a"), (12, 0.6, "b")]), [(10, 0.5, "a")])


class UartSecondsTest(unittest.TestCase):
    def test_hex_digits_plus_line_end_at_10_bits_per_char(self):
        self.assertAlmostEqual(uartSeconds(16, 9600), 5 * 10 / 9600)   # 4 hex + 1
        self.assertAlmostEqual(uartSeconds(10, 9600), 4 * 10 / 9600)   # 3 hex + 1


class EstimateLEsTest(unittest.TestCase):
    def test_formula_at_16_bit_16_iterations(self):
        # schedule(16) ends at shift 14 (repeats at 4 and 13) -> 4 mux stages per shifter
        self.assertEqual(cordic.schedule(16)[-1], 14)
        self.assertEqual(estimateLEs(16, 16), 6 * 16 + 2 * 16 * 4 + LE_OVERHEAD)

    def test_more_shift_stages_when_max_shift_needs_more_bits(self):
        # schedule(18) ends at shift 16 -> 5 stages
        self.assertEqual(cordic.schedule(18)[-1], 16)
        self.assertEqual(estimateLEs(16, 18), 6 * 16 + 2 * 16 * 5 + LE_OVERHEAD)


class MaxWidthForLEsTest(unittest.TestCase):
    def test_largest_width_within_budget(self):
        budget = estimateLEs(40, 40)
        self.assertEqual(maxWidthForLEs(budget), 40)
        self.assertEqual(maxWidthForLEs(budget - 1), 39)

    def test_budget_below_overhead_gives_zero(self):
        self.assertEqual(maxWidthForLEs(LE_OVERHEAD), 0)


class WidthSummaryTest(unittest.TestCase):
    def test_fields_match_direct_computation(self):
        ts = [-0.8, 0.1, 0.9]
        row = widthSummary("cosh", 12, 2, ts, 14, 50e6, 9600, 1e-2)
        errs = [worstError("cosh", n, 10, 12, ts) for n in range(1, 15)]
        n = bestByProduct(errs)
        self.assertEqual(row["width"], 12)
        self.assertEqual(row["frac"], 10)
        self.assertEqual(row["n"], n)
        self.assertEqual(row["cycles"], n + 1)
        self.assertAlmostEqual(row["time_s"], (n + 1) / 50e6)
        self.assertEqual(row["max_err"], errs[n - 1])
        self.assertAlmostEqual(row["bits"], -math.log2(errs[n - 1]))
        self.assertAlmostEqual(row["err_lsb"], errs[n - 1] * 2 ** 10)
        self.assertEqual(row["n_tol"], cheapestN(errs, 1e-2))
        self.assertEqual(row["lut_bits"], n * 12)
        self.assertEqual(row["reg_bits"], 36)
        self.assertEqual(row["les"], estimateLEs(12, n))
        self.assertAlmostEqual(row["uart_s"], uartSeconds(12, 9600))

    def test_width_must_exceed_int_bits(self):
        with self.assertRaises(ValueError):
            widthSummary("cosh", 2, 2, [0.1], 8, 50e6, 9600, 1e-2)


if __name__ == "__main__":
    unittest.main()
