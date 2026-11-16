# DE1 board docs

- `DE1_pin_assignments.csv`: official Terasic/Altera pin file (DE1 System CD). Source of truth for
  Quartus (Assignments > Import Assignments).
- `DE1_pin_table_from_manual.csv`: pin tables 4.1-4.18 pulled from `DE1_UserManual_v1017.pdf`, with
  descriptions and a column checking each pin against the official CSV.
- `DE1_pins.md` + `img/*.svg`: readable pin reference with diagrams (switches/LEDs, HEX, GPIO
  headers). Generated once from the two CSVs (pins from the official CSV); the generator was not kept.

## Lessons

- 2026-11-12: Extract this manual's pin tables with `pdftotext -raw`, not `-layout`, and always
  cross-check against `DE1_pin_assignments.csv`. Why: `-layout` dropped cells in the VGA, audio,
  SRAM, flash and clock tables, shifting pins one row (35 false mismatches).
