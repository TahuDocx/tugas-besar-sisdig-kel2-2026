# architecture

VHDL for the CORDIC datapath (Terasic DE1). Code lives in `datapath/<entity>/<entity>.vhd`.

- **Read `convention.md` (same folder) before writing or editing any `.vhd` here.** It holds the
  layout, file structure, style rules and the recorded convention deviations (Indonesian comments,
  naming). Treat it as part of this file.

## Lessons

- 2026-11-16: `register16bit.vhd` used `"x0000"` for a 16-bit zero (invalid literal). Use
  `(others => '0')` or `x"0000"`. Why: the `x` must be outside the quotes.
- 2026-11-16: Don't claim `x"0000"` needs VHDL-2008. Why: hex bit-string literals are valid in
  VHDL-93 when the length is a multiple of 4; I told the user otherwise.
- 2026-11-16: Compile-check VHDL before reporting it fixed. Why: no simulator is installed here,
  so these edits are unverified until Quartus/ModelSim runs them.
