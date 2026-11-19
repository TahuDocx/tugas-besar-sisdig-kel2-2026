"""Pure glue from the simulator form to ../cordic-sim-py/cordic.py (no Qt).

cordic-sim-py is imported from its sibling folder, not copied, so the GUI always runs the
same bit-exact model the tests and golden vectors check.
"""

import math
import sys
import time
from pathlib import Path

_SIM_DIR = Path(__file__).resolve().parent.parent / "cordic-sim-py"
if str(_SIM_DIR) not in sys.path:
    sys.path.append(str(_SIM_DIR))  # append: never displace the app's own sys.path[0]

import cordic  # noqa: E402  (needs the path above)

FUNCS = cordic.FUNCS


FPGA_OVERHEAD_CYCLES = 1  # IDLE -> ITER load clock (CORDIC_Hyperbolic_FPGA.md ASM chart)


# === SIMULATION ===

def simulate(func: str, t_text: str, n: int, use_fixed: bool, frac: int, width: int) -> str:
    """Runs cordic.compute for the form values and returns cordic.formatReport text.

    t_text is parsed as a float (surrounding whitespace ignored). frac/width are used only
    when use_fixed is True; then 2 <= width and 0 <= frac < width are required.
    Raises ValueError on unknown func, non-numeric or non-finite t, n < 1, or a bad fixed
    format. No side effects.
    """
    return simulateTimed(func, t_text, n, use_fixed, frac, width)[0]


def simulateTimed(func: str, t_text: str, n: int, use_fixed: bool, frac: int,
                  width: int) -> tuple:
    """Same as simulate(), but returns (report, seconds): seconds is the wall-clock time of
    cordic.compute alone (validation and formatting excluded), from time.perf_counter.
    Raises ValueError like simulate(). No side effects.
    """
    t, kwargs = _parseForm(func, t_text, n, use_fixed, frac, width)
    start = time.perf_counter()
    res = cordic.compute(func, t, n, **kwargs)
    seconds = time.perf_counter() - start
    return cordic.formatReport(res), seconds


def errorSweep(func: str, t_text: str, n_max: int, use_fixed: bool, frac: int,
               width: int) -> list:
    """Returns [[n, |value - expected|], ...] for n = 1 .. n_max, one cordic.compute per n
    (x0 = 1/K depends on n, so a single run's steps would not give the true error).

    Points whose error is not finite (expected undefined, e.g. atanh(1.5)) are left out, so
    the list may be shorter or empty. Raises ValueError like simulate(). No side effects.
    """
    t, kwargs = _parseForm(func, t_text, n_max, use_fixed, frac, width)
    points = []
    for n in range(1, n_max + 1):
        res = cordic.compute(func, t, n, **kwargs)
        err = abs(res.value - res.expected)
        if math.isfinite(err):
            points.append([n, err])
    return points


def minIterations(points: list, tol: float) -> int:
    """Returns the smallest n in points ([[n, err], ...], n ascending) from which every later
    point has err <= tol, or 0 if the last point is above tol or points is empty.

    A single early point under tol is ignored when a later one rises above it again (CORDIC
    error oscillates with n). Raises ValueError unless tol is finite and > 0. No side effects.
    """
    if not (math.isfinite(tol) and tol > 0):
        raise ValueError("tolerance must be a finite number > 0")
    best = 0
    for n, err in reversed(points):
        if err > tol:
            break
        best = n
    return best


def _parseForm(func: str, t_text: str, n: int, use_fixed: bool, frac: int,
               width: int) -> tuple:
    """Validates the form values and returns (t, compute kwargs). kwargs is {} for float,
    {"frac", "width"} for fixed. Raises ValueError as described in simulate(). No side
    effects."""
    if func not in FUNCS:
        raise ValueError(f"unknown function {func!r}")
    try:
        t = float(t_text.strip())
    except ValueError:
        raise ValueError(f"t is not a number: {t_text.strip()!r}") from None
    if not math.isfinite(t):
        raise ValueError("t must be finite")
    if n < 1:
        raise ValueError("n must be at least 1")
    if use_fixed:
        if width < 2:
            raise ValueError("width must be at least 2")
        if not 0 <= frac < width:
            raise ValueError("frac must be in 0 .. width-1")
        kwargs = {"frac": frac, "width": width}
    else:
        kwargs = {}
    return t, kwargs


# === TIMING ===

def fpgaCycles(n: int) -> int:
    """Returns clocks from start to result for the iterative core: 1 load + n iterations
    (one iteration per clock, ASM chart in CORDIC_Hyperbolic_FPGA.md). No side effects."""
    return FPGA_OVERHEAD_CYCLES + n


def fpgaTime(n: int, clock_mhz: float) -> float:
    """Returns the iterative core's latency in seconds at clock_mhz.
    Raises ValueError if clock_mhz <= 0. No side effects."""
    if not clock_mhz > 0:
        raise ValueError("clock must be > 0 MHz")
    return fpgaCycles(n) / (clock_mhz * 1e6)


def formatDuration(seconds: float) -> str:
    """Returns seconds as 3 significant digits in ns, µs, ms or s (e.g. "48.2 µs").
    Rounds before picking the unit, so 999.9 ns gives "1 µs". No side effects."""
    s = float(f"{seconds:.3g}")
    for unit, scale in (("s", 1.0), ("ms", 1e-3), ("µs", 1e-6)):
        if s >= scale:
            return f"{s / scale:.3g} {unit}"
    return f"{s / 1e-9:.3g} ns"
