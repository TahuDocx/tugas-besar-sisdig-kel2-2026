# cordic-interface

PySide6 + QML GUI that talks to the FPGA over UART (QtSerialPort, default 9600 8N1).

- Run: `.venv/Scripts/python.exe main.py`. Tests: `.venv/Scripts/python.exe -m unittest -v`.
- `serial_codec.py` = pure byte format (TDD, no Qt). `serial_backend.py` = QSerialPort bridge,
  exposed to QML as context property `serial`. UI in `CordicUI/Main.qml` (module `CordicUI`).
- Simulator window (`CordicUI/SimWindow.qml`, button "Simulator") runs `../cordic-sim-py/cordic.py`
  via `sim_runner.py` (imports the sibling folder, never copies it) + `sim_backend.py` (`sim`).
  Tab "Error vs iterations": QML `Canvas` log plot of `errorSweep` (n = 1 .. n) + min n from
  `minIterations` (error must stay <= tolerance for every later n, not just dip under once).
- Protocol is provisional: t sent as ASCII text + selectable line end; RX shown as ASCII,
  non-printables as `<HH>`. Change only `serial_codec.py` when the frame format is fixed.

## Convention deviations

- Same as `../cordic-sim-py/CLAUDE.md`: Python docstrings inside the `def`; functions
  `camelCase`. Qt property getters are private `_getX` and exposed via `Property`.
- QML: `//` comment directly above each JS function (QML has no docstring form).

## Lessons

- 2026-11-17: Never `sys.path.insert(0, ...)` in an imported module (use `append`), and locate
  app files with `Path(__file__)`, never `sys.path[0]`. Smoke-test by launching `main.py` itself,
  not a copy of its setup. Why: sim_runner's insert made main.py look for QML in cordic-sim-py
  ("No module named Example"); the smoke test set the import path itself, so it missed this.
- 2026-11-17: In QML never blanket-sed `var` -> `let`; it also rewrites `property var`
  (invalid). Edit JS `var`s only. Why: sed turned `property var fixedPts` into `property let`.
- 2026-11-17: In render/smoke scripts find QML controls with `o.inherits("QQuickTextField")`,
  never `className()` (styled controls are `TextField_QMLTYPE_n`). Import `PySide6.QtQuick`
  so the root is a `QQuickWindow` (has `grabWindow`). Why: two scratch renders found nothing.
