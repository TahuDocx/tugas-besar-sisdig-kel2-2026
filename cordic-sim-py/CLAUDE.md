# cordic-sim-py

Python port of `../cordic-sim/cordic.js` (core logic only, no UI). Used by `../cordic-interface`.

- Fixed-point results must stay bit-exact with the JS reference. After changing either side,
  regenerate `golden/golden.json` (`node cordic-sim-py/golden/gen_golden.js` from repo root)
  and run `python -m unittest -v` here.
- Tests use stdlib `unittest` (pytest is not installed).
- `iterative_vs_error_simulation.py`: worst-case-over-t error per (frac, n), picks n by
  argmin n*E and "no later gain >= 1 LSB" -> `iterative_vs_error_<func>.png`; per `--tol` the
  cheapest (frac, n) by cost width x (n+1) -> `format_choice_<func>.png`; `--widths 8 16 ...`
  compares total widths with DE1 limits -> `width_compare_<func>.png`. Needs matplotlib: run
  with python.org 3.13 (`py -3.13 ...`), not the cordic-interface venv.

## Convention deviations

- Docstrings: Python `"""docstring"""` inside the `def`, not a comment above the signature.
  Why: Python idiom; `help()` and IDE tooltips read it for cordic-interface. Banners are
  `# === GROUP ===` comments.
- Functions stay `camelCase` (global rule) although PEP 8 says `snake_case`.
  Dataclass fields are `snake_case` (variables).

## Lessons

- 2026-11-17: For "smallest n such that ..." pickers, scan forward and test each n; a backward
  scan with `break` gives "every n from here on", a different rule. Add a test where the
  two differ. Why: bestByDelta picked n=30 for Q2.6 (overflow recovery late in the sweep).
- 2026-11-17: Float test vectors that compare against a threshold use binary fractions
  (0.25, 0.1875, 0.0625). Why: `0.25 - 0.20 < 0.05` in float, so a correct picker failed.
