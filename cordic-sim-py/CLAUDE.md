# cordic-sim-py

Python port of `../cordic-sim/cordic.js` (core logic only, no UI). Used by `../cordic-interface`.

- Fixed-point results must stay bit-exact with the JS reference. After changing either side,
  regenerate `golden/golden.json` (`node cordic-sim-py/golden/gen_golden.js` from repo root)
  and run `python -m unittest -v` here.
- Tests use stdlib `unittest` (pytest is not installed).

## Convention deviations

- Docstrings: Python `"""docstring"""` inside the `def`, not a comment above the signature.
  Why: Python idiom; `help()` and IDE tooltips read it for cordic-interface. Banners are
  `# === GROUP ===` comments.
- Functions stay `camelCase` (global rule) although PEP 8 says `snake_case`.
  Dataclass fields are `snake_case` (variables).

## Lessons
