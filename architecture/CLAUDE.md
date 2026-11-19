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
- 2026-11-16: Compile-check VHDL before reporting it fixed, with Questa FSE
  `C:\altera_lite\25.1std\questa_fse\win64\vcom -93` (`vlib work` first; `vsim -c` for testbenches).
  Why: 2026-11-18 found this simulator installed; an earlier entry wrongly said none existed.
- 2026-11-19: Lay out port blocks from `convention.md` itself (closing `);` at 4 tabs, `:` and
  comment columns aligned at tab width 4), not by copying an existing file. Why: copied
  register16bit's old 3-tab `);` and ragged columns into mux16bit2to1/shifter16bit; review caught it.
