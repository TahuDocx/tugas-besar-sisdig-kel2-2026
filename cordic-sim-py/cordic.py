"""Hyperbolic CORDIC core. Python port of cordic-sim/cordic.js (pure logic, no UI).

Fixed-point mode is bit-exact integer math: what the VHDL datapath should produce.
Parity with the JS reference is checked by test_cordic.py against golden/golden.json.

Library use:  import cordic; r = cordic.compute("cosh", 0.5, 16, frac=14, width=16)
CLI use:      python cordic.py cosh 0.5 --n 16 --frac 14 --width 16
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from typing import Optional

FUNCS = ("cosh", "sinh", "exp", "atanh", "ln", "sqrt")
MODES = ("rotation", "vectoring")


# === TYPES ===

@dataclass(frozen=True)
class FixedFormat:
    """Fixed-point word: `frac` fraction bits inside a `width`-bit two's-complement register."""
    frac: int
    width: int


@dataclass(frozen=True)
class Step:
    """Register state after iteration k. Step 0 is the loaded input (i, d, xs, ys, a are None).

    i = shift amount, d = direction (+1/-1), xs/ys = shifted x/y, a = LUT angle used.
    Values are ints (raw register contents) in fixed mode, floats in float mode.
    """
    k: int
    i: Optional[int]
    d: Optional[int]
    x: float
    y: float
    z: float
    xs: Optional[float] = None
    ys: Optional[float] = None
    a: Optional[float] = None


@dataclass(frozen=True)
class RunResult:
    """One full CORDIC run: schedule, atanh LUT, every step, and the overflow flag.

    `scale` = 2^frac (1 in float mode); divide raw register values by it to get reals.
    """
    mode: str
    sched: list
    lut: list
    steps: list
    scale: float
    gain: float
    overflow: bool
    fixed: Optional[FixedFormat]


@dataclass(frozen=True)
class ComputeResult:
    """Result of computing one function: CORDIC value, math-library value, and domain limits."""
    value: float
    expected: float
    run: RunResult
    in_range: bool
    gain: float
    theta_max: float
    ratio_max: float


# === PRIMITIVES ===

def schedule(n: int, repeats: bool = True) -> list:
    """Returns the first n shift indices: 1,2,3,4,4,5,...,13,13,...,40,40,... (repeat k -> 3k+1).

    Without repeats hyperbolic CORDIC does not converge; repeats=False gives plain 1..n,
    only for demonstrating why repeats are needed. No side effects.
    """
    out = []
    rep = 4
    i = 1
    while len(out) < n:
        out.append(i)
        if repeats and i == rep and len(out) < n:
            out.append(i)
            rep = 3 * rep + 1
        i += 1
    return out


def gain(sched: list) -> float:
    """Returns K = prod sqrt(1 - 2^-2i) over the schedule (~0.82816). No side effects.

    Rotation mode starts at x0 = 1/K to cancel it.
    """
    k = 1.0
    for i in sched:
        k *= math.sqrt(1 - 2.0 ** (-2 * i))
    return k


def ashr(v: int, s: int) -> int:
    """Returns v arithmetically shifted right by s (floor division by 2^s, like VHDL
    shift_right on signed / Verilog >>>). No side effects."""
    return v >> s


def wrap(v: int, width: int) -> int:
    """Returns v wrapped to a `width`-bit two's-complement value (register overflow).
    No side effects."""
    m = 1 << width
    h = m >> 1
    return ((v + h) % m) - h


def jsRound(v: float) -> int:
    """Returns v rounded half toward +inf as an int, matching JS Math.round
    (Python round() is banker's rounding and would break bit parity). No side effects."""
    return math.floor(v + 0.5)


def thetaMax(n: int) -> float:
    """Returns the rotation-mode domain limit: sum of atanh(2^-i) over the schedule
    (~1.1182 for any useful n). No side effects."""
    return sum(math.atanh(2.0 ** -i) for i in schedule(n))


# === CORE ===

def run(mode: str, x0: float, y0: float, z0: float, n: int,
        fixed: Optional[FixedFormat] = None) -> RunResult:
    """Runs n hyperbolic CORDIC iterations and returns every step.

    mode 'rotation' drives z -> 0, 'vectoring' drives y -> 0. fixed=None runs in float;
    otherwise inputs and LUT are quantized to `fixed` and every register write wraps to
    fixed.width bits (overflow flag set if any wrap changed a value). Raises ValueError on
    unknown mode. No other side effects.
    """
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}, expected one of {MODES}")
    sched = schedule(n)
    scale = 2 ** fixed.frac if fixed else 1
    overflow = False

    def q(v):
        nonlocal overflow
        if not fixed:
            return v
        w = wrap(v, fixed.width)
        if w != v:
            overflow = True
        return w

    def load(v):
        return q(jsRound(v * scale)) if fixed else v

    def shr(v, s):
        return ashr(v, s) if fixed else v * 2.0 ** -s

    lut = [load(math.atanh(2.0 ** -i)) for i in sched]
    x, y, z = load(x0), load(y0), load(z0)
    steps = [Step(k=0, i=None, d=None, x=x, y=y, z=z)]

    for k, i in enumerate(sched):
        if mode == "rotation":
            d = 1 if z >= 0 else -1
        else:
            d = 1 if y < 0 else -1
        xs, ys = shr(x, i), shr(y, i)
        x, y, z = q(x + d * ys), q(y + d * xs), q(z - d * lut[k])
        steps.append(Step(k=k + 1, i=i, d=d, x=x, y=y, z=z, xs=xs, ys=ys, a=lut[k]))

    return RunResult(mode=mode, sched=sched, lut=lut, steps=steps, scale=scale,
                     gain=gain(sched), overflow=overflow, fixed=fixed)


def compute(func: str, t: float, n: int, frac: Optional[int] = None,
            width: Optional[int] = None) -> ComputeResult:
    """Computes func(t) with n CORDIC iterations and returns the value plus the full run.

    func is one of FUNCS. Pass frac and width together for the fixed-point datapath, neither
    for float. in_range is False when t is outside the domain CORDIC converges on.
    Raises ValueError on unknown func or when only one of frac/width is given.
    """
    if (frac is None) != (width is None):
        raise ValueError("give both frac and width (fixed) or neither (float)")
    fixed = FixedFormat(frac, width) if frac is not None else None
    k_gain = gain(schedule(n))
    tm = thetaMax(n)
    r_max = math.tanh(tm)

    if func in ("cosh", "sinh", "exp"):
        r = run("rotation", 1 / k_gain, 0, t, n, fixed)
        last = r.steps[-1]
        in_range = abs(t) <= tm
        raw = {"cosh": last.x, "sinh": last.y, "exp": last.x + last.y}[func]
        value = raw / r.scale
        expected = getattr(math, func)(t)
    elif func == "atanh":
        r = run("vectoring", 1, t, 0, n, fixed)
        in_range = abs(t) <= r_max
        value = r.steps[-1].z / r.scale
        expected = math.atanh(t) if abs(t) < 1 else math.nan
    elif func == "ln":  # ln w = 2 * atanh((w-1)/(w+1))
        r = run("vectoring", t + 1, t - 1, 0, n, fixed)
        in_range = t > 0 and abs((t - 1) / (t + 1)) <= r_max
        value = 2 * (r.steps[-1].z / r.scale)
        expected = math.log(t) if t > 0 else math.nan
    elif func == "sqrt":  # sqrt w = sqrt((w+1/4)^2 - (w-1/4)^2); vectoring gives K*sqrt(.)
        r = run("vectoring", t + 0.25, t - 0.25, 0, n, fixed)
        in_range = t > 0 and abs((t - 0.25) / (t + 0.25)) <= r_max
        xn = r.steps[-1].x
        if fixed:
            value = ashr(xn * jsRound(r.scale / k_gain), fixed.frac) / r.scale
        else:
            value = xn / k_gain
        expected = math.sqrt(t) if t >= 0 else math.nan
    else:
        raise ValueError(f"unknown func {func!r}, expected one of {FUNCS}")

    return ComputeResult(value=value, expected=expected, run=r, in_range=in_range,
                         gain=k_gain, theta_max=tm, ratio_max=r_max)


# === CLI ===

def formatReport(res: ComputeResult) -> str:
    """Returns a printable iteration table (raw registers + real values) and result summary.
    No side effects."""
    r = res.run
    fx = r.fixed
    hexw = (fx.width + 3) // 4 if fx else 0

    def raw(v):
        return f"{v & ((1 << fx.width) - 1):0{hexw}X}" if fx else ""

    fmt = f"Q{fx.width - fx.frac}.{fx.frac} ({fx.width}-bit)" if fx else "float"
    lines = [f"mode {r.mode}, format {fmt}, K = {res.gain:.10f}", ""]
    head = f"{'k':>3} {'i':>3} {'d':>2}  {'x':>12} {'y':>12} {'z':>12}"
    if fx:
        head += f"  {'x_hex':>{hexw}} {'y_hex':>{hexw}} {'z_hex':>{hexw}}"
    lines.append(head)
    for s in r.steps:
        i = "" if s.i is None else s.i
        d = "" if s.d is None else f"{s.d:+d}"
        row = (f"{s.k:>3} {i:>3} {d:>2}  {s.x / r.scale:>12.8f} {s.y / r.scale:>12.8f}"
               f" {s.z / r.scale:>12.8f}")
        if fx:
            row += f"  {raw(s.x):>{hexw}} {raw(s.y):>{hexw}} {raw(s.z):>{hexw}}"
        lines.append(row)
    err = res.value - res.expected
    lines += ["",
              f"result   {res.value:.10f}",
              f"expected {res.expected:.10f}",
              f"error    {err:.3e}",
              f"in range {res.in_range}   overflow {r.overflow}"]
    return "\n".join(lines)


def main(argv: Optional[list] = None) -> int:
    """CLI entry: parses argv, prints the report to stdout, returns the exit code (0 = ok,
    2 = bad arguments via argparse)."""
    p = argparse.ArgumentParser(description="Hyperbolic CORDIC simulator (Python port).")
    p.add_argument("func", choices=FUNCS)
    p.add_argument("t", type=float, help="input value")
    p.add_argument("--n", type=int, default=16, help="iterations (default 16)")
    p.add_argument("--frac", type=int, default=14, help="fraction bits (default 14)")
    p.add_argument("--width", type=int, default=16, help="register width (default 16)")
    p.add_argument("--float", action="store_true", help="ideal float instead of fixed-point")
    a = p.parse_args(argv)
    if a.float:
        res = compute(a.func, a.t, a.n)
    else:
        res = compute(a.func, a.t, a.n, frac=a.frac, width=a.width)
    print(formatReport(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
