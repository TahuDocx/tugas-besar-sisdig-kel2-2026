# architecture: VHDL conventions

Derived from the existing code in `datapath/` (`register16bit`, `counter4bit`, `fullAdder16bit`).
Global rules in `~/.claude/CLAUDE.md` still apply except where "Convention deviations" says otherwise.

## Layout

- One entity per folder: `datapath/<entity>/<entity>.vhd`. Folder, file and entity name are identical.
- Entity names: `camelCase` with the bit width as suffix (`register16bit`, `counter4bit`,
  `fullAdder16bit`).
- Target board: Terasic DE1 (Cyclone II). Pins: `docs/de1/`.

## File structure (follow `register16bit.vhd` / `counter4bit.vhd`)

1. `-- Library` banner, then `library ieee; use ieee.std_logic_1164.all; use ieee.numeric_std.all;`
   (drop `numeric_std` if unused).
2. `-- Define entity` banner, then the entity.
3. `-- Define architecture` banner, then the architecture.

## Style

- Keywords lowercase (`entity`, `port`, `signal`, `rising_edge`).
- Indent with tabs. Port block: `port<tab>(` then one port per line, indented 4 tabs and
  tab-aligned as `Name : dir type`, closing `);` indented 4 tabs too, one `--` comment per port.
- Architecture name `rtl` for clocked or register-style logic. `behavioral` for pure combinational
  logic.
- Port names `PascalCase`: `En` (enable), `Res` (reset, synchronous, active high), `Clk` (clock),
  `A`/`B` (data in), `Data`/`Count`/`S` (data out). Keep this order for control ports: `En, Res, Clk`.
- Internal signals: `v_` prefix + `snake_case` (`v_data`, `v_count`, `v_carry`). A typed copy of
  an output (`unsigned` for arithmetic) is cast on assignment to the port.
- Sequential process: sensitivity list `(Clk)` only, `if rising_edge(Clk)`, synchronous reset
  checked first (reset beats enable), then enable. Output is a concurrent assignment from the internal
  signal below the process.
- Zero values: `(others => '0')` or `x"0000"` (hex literal, valid in VHDL-93, length multiple of 4).
  Never `"x0000"`.
- Write `if (cond)` and `rising_edge(Clk)` with the same spacing everywhere.
- Prefer `for ... generate` over copy-pasted bit slices.
- Import `numeric_std` only if the file uses `unsigned`/`signed`.
- A comment above every process, `if` branch and concurrent assignment saying what it does.
- No tests exist yet. Proposed: `<entity>/<entity>_tb.vhd`, entity `<entity>_tb`. Confirm before use.

## Convention deviations

- Comments are in **Indonesian** (existing code), not English. Why: all existing `.vhd` comments are.
  Keep Indonesian for `.vhd` in this folder. Identifiers stay English.
- VHDL has no `.h`/C-style docstrings, so the global docstring rule is replaced by the per-port
  and per-block `--` comments above.
- Naming: ports `PascalCase`, entities `camelCase`, signals `snake_case`. This replaces the global
  "`PascalCase` types only" rule. Why: it matches existing code and the DE1/Quartus habit.
- None else. `fullAdder16bit.vhd` was restyled to match (2026-11-16); it keeps the ripple-carry
  structure via a `generate` loop.
