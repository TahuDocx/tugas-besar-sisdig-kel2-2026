"""Tests for cordic.py. Run from cordic-sim-py/: python -m unittest -v

Port of cordic-sim/cordic.test.js, plus bit-exact parity against golden/golden.json
(generated from the JS reference by golden/gen_golden.js).
"""
import contextlib
import io
import json
import math
import pathlib
import unittest

import cordic as C

GOLDEN = json.loads((pathlib.Path(__file__).parent / "golden" / "golden.json").read_text())


class TestPrimitives(unittest.TestCase):
    def test_scheduleRepeats4_13_40(self):
        self.assertEqual(C.schedule(6), [1, 2, 3, 4, 4, 5])
        s = C.schedule(16)
        self.assertEqual(len(s), 16)
        self.assertEqual([v for v in s if v == 13], [13, 13])
        self.assertEqual([v for v in C.schedule(45) if v == 40], [40, 40])

    def test_scheduleWithoutRepeatsIsPlain(self):
        self.assertEqual(C.schedule(6, repeats=False), [1, 2, 3, 4, 5, 6])

    def test_withoutRepeatsSomeAnglesUnreachable(self):
        def zEnd(sched, t):
            z = t
            for i in sched:
                z -= (1 if z >= 0 else -1) * math.atanh(2.0 ** -i)
            return z

        self.assertGreater(abs(zEnd(C.schedule(16, repeats=False), 0.55)), 1e-3)
        self.assertLess(abs(zEnd(C.schedule(17), 0.55)), 1e-4)

    def test_gainConverges(self):
        self.assertAlmostEqual(C.gain(C.schedule(30)), 0.8281593609602, delta=1e-9)

    def test_ashrFloorsLikeVerilog(self):
        self.assertEqual(C.ashr(-5, 1), -3)
        self.assertEqual(C.ashr(5, 1), 2)
        self.assertEqual(C.ashr(-1, 4), -1)

    def test_wrapTwosComplement(self):
        self.assertEqual(C.wrap(32768, 16), -32768)
        self.assertEqual(C.wrap(-32769, 16), 32767)
        self.assertEqual(C.wrap(123, 16), 123)

    def test_jsRoundHalfUp(self):
        # Must match JS Math.round, not Python's banker's round().
        self.assertEqual(C.jsRound(2.5), 3)
        self.assertEqual(C.jsRound(-2.5), -2)
        self.assertEqual(C.jsRound(0.5), 1)
        self.assertEqual(C.jsRound(-0.5), 0)
        self.assertIsInstance(C.jsRound(1.2), int)


class TestCompute(unittest.TestCase):
    def test_floatRotation(self):
        for t in (-1, -0.3, 0, 0.5, 1.1):
            self.assertAlmostEqual(C.compute("cosh", t, 24).value, math.cosh(t), delta=1e-6)
            self.assertAlmostEqual(C.compute("sinh", t, 24).value, math.sinh(t), delta=1e-6)
            self.assertAlmostEqual(C.compute("exp", t, 24).value, math.exp(t), delta=1e-6)

    def test_floatVectoring(self):
        self.assertAlmostEqual(C.compute("atanh", 0.5, 24).value, math.atanh(0.5), delta=1e-6)
        for w in (0.2, 1, 2, 5):
            self.assertAlmostEqual(C.compute("ln", w, 24).value, math.log(w), delta=1e-5)
        for w in (0.1, 1, 2):
            self.assertAlmostEqual(C.compute("sqrt", w, 24).value, math.sqrt(w), delta=1e-5)

    def test_outOfDomainFlagged(self):
        self.assertFalse(C.compute("sqrt", 5, 24).in_range)
        self.assertFalse(C.compute("cosh", 2, 24).in_range)
        self.assertTrue(C.compute("cosh", 1, 24).in_range)
        self.assertFalse(C.compute("ln", -1, 24).in_range)

    def test_fixedIsIntegerDatapath(self):
        o = dict(n=16, frac=16, width=24)
        self.assertAlmostEqual(C.compute("cosh", 0.5, **o).value, math.cosh(0.5), delta=5e-4)
        self.assertAlmostEqual(C.compute("sinh", -0.8, **o).value, math.sinh(-0.8), delta=5e-4)
        self.assertAlmostEqual(C.compute("ln", 2, **o).value, math.log(2), delta=5e-4)
        r = C.compute("cosh", 0.5, **o).run
        for s in r.steps:
            for v in (s.x, s.y, s.z):
                self.assertIs(type(v), int)
        self.assertTrue(all(type(a) is int for a in r.lut))
        self.assertFalse(r.overflow)

    def test_fixedOverflowFlagged(self):
        # sqrt(9): x0 = 9.25 -> 9.25 * 2^14 > 2^15 - 1 in a 16-bit word
        self.assertTrue(C.compute("sqrt", 9, 12, frac=14, width=16).run.overflow)

    def test_badArgumentsRaise(self):
        with self.assertRaises(ValueError):
            C.compute("tan", 0.5, 16)
        with self.assertRaises(ValueError):
            C.compute("cosh", 0.5, 16, frac=14)  # width missing
        with self.assertRaises(ValueError):
            C.run("circular", 1, 0, 0, 8)

    def test_resultsAreImmutable(self):
        r = C.compute("cosh", 0.5, 16, frac=14, width=16)
        with self.assertRaises(AttributeError):
            r.value = 0
        with self.assertRaises(AttributeError):
            r.run.steps[0].x = 0


class TestGoldenParity(unittest.TestCase):
    """Every golden case must match the JS reference: fixed bit-exact, float to 1e-12."""

    def test_allGoldenCases(self):
        self.assertEqual(len(GOLDEN), 85)
        for case in GOLDEN:
            opts = case["opts"]
            fixed = "frac" in opts
            label = f"{case['func']}({case['t']}) {opts}"
            with self.subTest(label):
                r = C.compute(case["func"], case["t"], opts["n"],
                              frac=opts.get("frac"), width=opts.get("width"))
                g = case["run"]
                self.assertEqual(r.run.mode, g["mode"])
                self.assertEqual(r.run.sched, g["sched"])
                self.assertEqual(r.run.overflow, g["overflow"])
                self.assertEqual(r.in_range, case["inRange"])
                self.assertEqual(len(r.run.steps), len(g["steps"]))
                same = self.assertEqual if fixed else (
                    lambda a, b: self.assertAlmostEqual(a, b, delta=1e-12))
                for a, b in zip(r.run.lut, g["lut"]):
                    same(a, b)
                for s, gs in zip(r.run.steps, g["steps"]):
                    self.assertEqual(s.i, gs["i"])
                    self.assertEqual(s.d, gs["d"])
                    for key in ("x", "y", "z", "xs", "ys", "a"):
                        if key in gs:
                            same(getattr(s, key), gs[key])
                same(r.value, case["value"])
                self.assertAlmostEqual(r.gain, case["K"], delta=1e-15)
                self.assertAlmostEqual(r.theta_max, case["thetaMax"], delta=1e-15)


class TestCli(unittest.TestCase):
    def test_mainPrintsTableAndResult(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = C.main(["cosh", "0.5", "--n", "16", "--frac", "14", "--width", "16"])
        text = out.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("result", text)
        self.assertIn("1.1276", text)  # cosh(0.5) = 1.12762...
        self.assertEqual(sum(1 for line in text.splitlines() if line.strip().startswith("16 ")), 1)

    def test_mainFloat(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = C.main(["ln", "2", "--float", "--n", "24"])
        self.assertEqual(code, 0)
        self.assertIn("0.6931", out.getvalue())


if __name__ == "__main__":
    unittest.main()
