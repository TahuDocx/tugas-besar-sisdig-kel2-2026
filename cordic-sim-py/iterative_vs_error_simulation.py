"""Iterations vs error sweep: picks the CORDIC iteration count n for each fraction width.

For every frac in a range (register width = frac + int_bits) and every n = 1 .. n_max, runs
the bit-exact fixed-point model (cordic.py) over a grid of t across the function's whole
convergence domain and keeps the WORST |error|. One t is not enough: per-t error oscillates
with n and a lucky dip picks an n that fails for other inputs.

Two pickers on that worst-case curve E(n):
  bestByProduct: argmin n * E(n)  (cost = iterations x error; lands where E first bottoms out)
  bestByDelta:   smallest n after which no extra iteration improves E by >= 1 LSB

CLI use:  python iterative_vs_error_simulation.py --func cosh --frac-min 6 --frac-max 20
Writes a PNG (needs matplotlib) and prints the per-frac table.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Optional

import cordic

DOMAIN_N = 64            # n used for the convergence domain (theta_max has converged by then)
EDGE_MARGIN = 1e-12      # keeps vectoring-grid endpoints strictly inside the ratio limit

# DE1 board, DE1_UserManual_v1017 sec. 2.1-2.2 (Cyclone II 2C20; sec. 2.2 misprints "2C35")
DE1_LES = 18752          # logic elements (one 4-input LUT + one flip-flop each)
DE1_M4K_BLOCKS = 52      # 4096-bit RAM blocks, 240K bits total
DE1_CLOCK_HZ = 50e6      # CLOCK_50 oscillator
UART_BITS_PER_CHAR = 10  # 8N1: start + 8 data + stop
LE_OVERHEAD = 400        # rough guess: FSM, iteration counter, UART, ASCII-hex, 7-seg driver


# === INPUT GRID ===

def tGrid(func: str, points: int) -> list:
    """Returns `points` ascending t values spanning func's convergence domain.

    cosh/sinh/exp: linear on [-theta_max, theta_max]; atanh: linear on [-r, r] with
    r = tanh(theta_max); ln/sqrt: geometric between the limits of |(t-c)/(t+c)| <= r
    (c = 1 for ln, 1/4 for sqrt). Raises ValueError on unknown func or points < 2.
    No side effects.
    """
    if func not in cordic.FUNCS:
        raise ValueError(f"unknown func {func!r}, expected one of {cordic.FUNCS}")
    if points < 2:
        raise ValueError("points must be at least 2")
    tm = cordic.thetaMax(DOMAIN_N)
    r = math.tanh(tm) * (1 - EDGE_MARGIN)
    if func in ("cosh", "sinh", "exp"):
        return _linspace(-tm, tm, points)
    if func == "atanh":
        return _linspace(-r, r, points)
    c = 1.0 if func == "ln" else 0.25
    lo, hi = c * (1 - r) / (1 + r), c * (1 + r) / (1 - r)
    return [lo * (hi / lo) ** (k / (points - 1)) for k in range(points)]


def _linspace(a: float, b: float, points: int) -> list:
    """Returns `points` evenly spaced values from a to b inclusive. No side effects."""
    return [a + (b - a) * k / (points - 1) for k in range(points)]


# === SWEEP ===

def worstError(func: str, n: int, frac: int, width: int, ts: list) -> float:
    """Returns max |value - expected| over ts for func with n iterations in fixed point
    (frac fraction bits, width-bit registers). Overflowed runs count with their real
    (wrong) value. Raises ValueError if ts is empty. No side effects."""
    if not ts:
        raise ValueError("ts must not be empty")
    worst = 0.0
    for t in ts:
        res = cordic.compute(func, t, n, frac=frac, width=width)
        worst = max(worst, abs(res.value - res.expected))
    return worst


def errorTable(func: str, fracs: list, n_max: int, int_bits: int, ts: list) -> dict:
    """Returns {frac: [E(1), ..., E(n_max)]} with E(n) = worstError(func, n, frac,
    frac + int_bits, ts). No side effects."""
    return {frac: [worstError(func, n, frac, frac + int_bits, ts) for n in range(1, n_max + 1)]
            for frac in fracs}


# === PICKERS ===

def bestByProduct(errs: list) -> int:
    """Returns the n (1-based) minimising n * errs[n-1]; the smallest n on ties.
    Raises ValueError if errs is empty. No side effects."""
    if not errs:
        raise ValueError("errs must not be empty")
    products = [(k + 1) * e for k, e in enumerate(errs)]
    return products.index(min(products)) + 1


def errorDeltas(errs: list) -> list:
    """Returns [errs[0] - errs[1], errs[1] - errs[2], ...]: the improvement each extra
    iteration gives (negative = got worse). Empty for fewer than 2 values. No side effects."""
    return [errs[k - 1] - errs[k] for k in range(1, len(errs))]


def bestByDelta(errs: list, lsb: float) -> int:
    """Returns the smallest n (1-based) such that no later n' improves on errs[n-1] by
    lsb or more (errs[n-1] - errs[n'-1] < lsb for all n' > n).

    Compares against every later n, not just the next one, so a near-flat step at a
    repeated shift does not stop the search early; a later blow-up that partly recovers
    (overflow) does not move the pick either. The last n always qualifies. Raises
    ValueError if errs is empty or lsb <= 0. No side effects.
    """
    if not errs:
        raise ValueError("errs must not be empty")
    if not lsb > 0:
        raise ValueError("lsb must be > 0")
    later_min = [math.inf] * len(errs)       # later_min[k] = min(errs[k+1:])
    for k in range(len(errs) - 2, -1, -1):
        later_min[k] = min(later_min[k + 1], errs[k + 1])
    for k, e in enumerate(errs):
        if e - later_min[k] < lsb:
            return k + 1
    return len(errs)  # unreachable: later_min[-1] is inf


# === FORMAT CHOICE ===

def cheapestN(errs: list, tol: float) -> int:
    """Returns the smallest n (1-based) with errs[n-1] <= tol, or 0 if none. errs are
    worst-case over t, and hardware runs a fixed n, so later n do not matter. Raises
    ValueError unless tol is finite and > 0. No side effects."""
    if not (math.isfinite(tol) and tol > 0):
        raise ValueError("tol must be a finite number > 0")
    for k, e in enumerate(errs):
        if e <= tol:
            return k + 1
    return 0


def atCost(frac: int, n: int, int_bits: int) -> int:
    """Returns the area-time cost width * cycles of the iterative core: width = frac +
    int_bits (registers, adders, shifters scale with it), cycles = 1 load + n iterations.
    No side effects."""
    return (frac + int_bits) * (1 + n)


def pickFormat(table: dict, int_bits: int, tol: float) -> Optional[tuple]:
    """Returns (frac, n) with the lowest atCost among formats in table ({frac: errs}) that
    reach tol, each at its cheapestN; ties go to the narrower width. None if no format
    reaches tol. Raises ValueError like cheapestN. No side effects."""
    best = None
    for frac in sorted(table):
        n = cheapestN(table[frac], tol)
        if n == 0:
            continue
        key = (atCost(frac, n, int_bits), frac)
        if best is None or key < best[0]:
            best = (key, (frac, n))
    return None if best is None else best[1]


def paretoFront(points: list) -> list:
    """Returns the non-dominated points of [(cost, err, ...extra), ...], sorted by cost:
    a point stays only if no other point is as cheap or cheaper with lower error (at equal
    cost only the lowest error stays). Extra tuple fields pass through. No side effects."""
    front = []
    for p in sorted(points, key=lambda q: (q[0], q[1])):
        if front and p[0] == front[-1][0]:
            continue                    # same cost, higher (or equal) error
        if not front or p[1] < front[-1][1]:
            front.append(p)
    return front


# === WIDTH COMPARISON ===

def uartSeconds(width: int, baud: float) -> float:
    """Returns the time to send one width-bit result over 8N1 UART as ASCII hex plus one
    line-end char: (ceil(width / 4) + 1) * 10 / baud. No side effects."""
    return (math.ceil(width / 4) + 1) * UART_BITS_PER_CHAR / baud


def estimateLEs(width: int, n: int) -> int:
    """Returns a rough Cyclone II logic-element count for the iterative datapath at width
    bits and n iterations: 3 add/sub (1 LE per bit, carry chain) + 3 load muxes (1 LE per
    bit) + 2 barrel shifters (one 2:1 mux LE per bit per stage, stages = bits of the largest
    shift in schedule(n)) + LE_OVERHEAD. The atanh LUT goes to M4K RAM, not LEs. An
    estimate only: Quartus synthesis gives the real count. No side effects."""
    stages = cordic.schedule(n)[-1].bit_length()
    return 6 * width + 2 * width * stages + LE_OVERHEAD


def maxWidthForLEs(budget: int) -> int:
    """Returns the largest width W with estimateLEs(W, W) <= budget (best n is about
    frac + 2 = W for 2 integer bits), or 0 if even W = 1 does not fit. No side effects."""
    w = 0
    while estimateLEs(w + 1, w + 1) <= budget:
        w += 1
    return w


def widthSummary(func: str, width: int, int_bits: int, ts: list, n_max: int,
                 clock_hz: float, baud: float, tol: float) -> dict:
    """Returns one comparison row for a width-bit datapath (frac = width - int_bits) at its
    bestByProduct n over 1 .. n_max, with keys: width, frac, n, cycles (n + 1), time_s,
    max_err, bits (-log2 max_err), digits (-log10 max_err), err_lsb, n_tol (cheapestN for
    tol, 0 = not reached), lut_bits (n * width), reg_bits (3 * width), les (estimateLEs),
    uart_s (uartSeconds). Raises ValueError if width <= int_bits, or like cheapestN.
    No side effects."""
    if width <= int_bits:
        raise ValueError("width must be larger than int_bits")
    frac = width - int_bits
    errs = [worstError(func, n, frac, width, ts) for n in range(1, n_max + 1)]
    n = bestByProduct(errs)
    e = errs[n - 1]
    return {"width": width, "frac": frac, "n": n, "cycles": n + 1,
            "time_s": (n + 1) / clock_hz, "max_err": e,
            "bits": -math.log2(e) if e > 0 else math.inf,
            "digits": -math.log10(e) if e > 0 else math.inf,
            "err_lsb": e * 2 ** frac, "n_tol": cheapestN(errs, tol),
            "lut_bits": n * width, "reg_bits": 3 * width, "les": estimateLEs(width, n),
            "uart_s": uartSeconds(width, baud)}


# === OUTPUT ===

def formatTable(func: str, table: dict, int_bits: int) -> str:
    """Returns the per-frac summary: format, both picked n, and E at those n in LSB.
    No side effects."""
    lines = [f"func {func}, worst |error| over the convergence domain, width = frac + {int_bits}",
             "",
             f"{'frac':>4} {'format':>8}  {'n(n*E)':>6} {'E [LSB]':>8}  "
             f"{'n(dE<1LSB)':>10} {'E [LSB]':>8}  {'min E [LSB]':>11} {'at n':>4}"]
    for frac, errs in table.items():
        lsb = 2.0 ** -frac
        n_p, n_d = bestByProduct(errs), bestByDelta(errs, lsb)
        e_min = min(errs)
        lines.append(f"{frac:>4} {'Q' + str(int_bits) + '.' + str(frac):>8}  {n_p:>6} "
                     f"{errs[n_p - 1] / lsb:>8.1f}  {n_d:>10} {errs[n_d - 1] / lsb:>8.1f}  "
                     f"{e_min / lsb:>11.1f} {errs.index(e_min) + 1:>4}")
    return "\n".join(lines)


def formatChoice(table: dict, int_bits: int, tols: list) -> str:
    """Returns, per tolerance, the pickFormat choice (format, n, cycles, worst error, AT
    cost) plus the runner-up formats within 10 % of its cost. No side effects."""
    lines = [f"cheapest format per tolerance (cost = width x cycles, width = frac + {int_bits},"
             " cycles = n + 1)", "",
             f"{'tol':>8}  {'format':>7} {'width':>5} {'n':>3} {'cycles':>6} {'max|err|':>9} "
             f"{'cost':>5}   close (within 10 %)"]
    for tol in tols:
        pick = pickFormat(table, int_bits, tol)
        if pick is None:
            lines.append(f"{tol:>8.0e}  not reached by any frac / n in the sweep")
            continue
        frac, n = pick
        cost = atCost(frac, n, int_bits)
        close = []
        for f in sorted(table):
            m = cheapestN(table[f], tol)
            if m and f != frac and atCost(f, m, int_bits) <= 1.1 * cost:
                close.append(f"Q{int_bits}.{f} n={m} ({atCost(f, m, int_bits)})")
        lines.append(f"{tol:>8.0e}  {'Q' + str(int_bits) + '.' + str(frac):>7} "
                     f"{frac + int_bits:>5} {n:>3} {n + 1:>6} {table[frac][n - 1]:>9.2e} "
                     f"{cost:>5}   {', '.join(close) or '-'}")
    return "\n".join(lines)


def formatWidths(func: str, rows: list, int_bits: int, tol: float, clock_hz: float,
                 baud: float) -> str:
    """Returns the width comparison table for widthSummary rows plus the DE1 limits
    footer (LE budget, M4K, double-precision model limit, display, switches).
    No side effects."""
    lines = [f"func {func}, {int_bits} integer bits, n = argmin n*E, clock "
             f"{clock_hz / 1e6:g} MHz, UART {baud:g} baud (ASCII hex + line end)", "",
             f"{'width':>5} {'format':>7} {'n':>3} {'cycles':>6} {'compute':>8} {'UART':>8} "
             f"{'max|err|':>9} {'bits':>5} {'digits':>6} {'n<=' + format(tol, 'g'):>8} "
             f"{'LUT bits':>8} {'~LEs':>5} {'% DE1':>6}"]
    for r in rows:
        lines.append(
            f"{r['width']:>5} {'Q' + str(int_bits) + '.' + str(r['frac']):>7} {r['n']:>3} "
            f"{r['cycles']:>6} {r['time_s'] * 1e9:>6.0f}ns {r['uart_s'] * 1e3:>6.2f}ms "
            f"{r['max_err']:>9.2e} {r['bits']:>5.1f} {r['digits']:>6.1f} "
            f"{r['n_tol'] if r['n_tol'] else '-':>8} {r['lut_bits']:>8} {r['les']:>5} "
            f"{r['les'] / DE1_LES:>6.1%}")
    lines += ["",
              "DE1 limits (DE1_UserManual_v1017 sec. 2.1-2.2, 4.3; LE counts are estimates):",
              f"  logic   : {DE1_LES} LEs -> about {maxWidthForLEs(DE1_LES)} bits by the "
              f"estimateLEs model (not the limit)",
              f"  memory  : {DE1_M4K_BLOCKS} M4K x 4096 bits; atanh LUT n x width fits one block "
              f"up to 64 x 64",
              "  model   : LUT built from double atanh and the JS golden model use doubles "
              "-> above ~52 fraction bits neither is exact",
              "  display : 4 seven-segment digits = 16 bits as hex; 10 switches = 10-bit input",
              "  timing  : max clock of wide adders/shifters needs Quartus 13.0sp1 (Cyclone II)"]
    return "\n".join(lines)


def plotWidths(func: str, rows: list, int_bits: int, out_path: Path) -> None:
    """Writes a 2x2 bar-chart PNG to out_path comparing the width rows: worst |error| (log),
    compute vs UART time (log), iterations n, and estimated LEs as % of the DE1. Imports
    matplotlib here. Side effect: writes out_path."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [f"{r['width']}-bit\nQ{int_bits}.{r['frac']}" for r in rows]
    xs = list(range(len(rows)))
    fig, ((ax_e, ax_t), (ax_n, ax_l)) = plt.subplots(2, 2, figsize=(13, 9))

    bars = ax_e.bar(xs, [r["max_err"] for r in rows], color="tab:red")
    ax_e.set_yscale("log")
    ax_e.bar_label(bars, labels=[f"{r['max_err']:.1e}\n({r['digits']:.1f} digits)"
                                 for r in rows], fontsize=8)
    ax_e.set(title="Worst-case |error| at best n", ylabel="max |error| (log)")

    w = 0.38
    b1 = ax_t.bar([x - w / 2 for x in xs], [r["time_s"] * 1e9 for r in rows], w,
                  label="CORDIC compute (n + 1 cycles)", color="tab:blue")
    b2 = ax_t.bar([x + w / 2 for x in xs], [r["uart_s"] * 1e9 for r in rows], w,
                  label="UART send of the result", color="tab:gray")
    ax_t.set_yscale("log")
    ax_t.bar_label(b1, labels=[f"{r['time_s'] * 1e9:.0f} ns" for r in rows], fontsize=8)
    ax_t.bar_label(b2, labels=[f"{r['uart_s'] * 1e3:.1f} ms" for r in rows], fontsize=8)
    ax_t.set(title="Time per result", ylabel="time [ns] (log)")
    ax_t.legend(fontsize=8)

    bars = ax_n.bar(xs, [r["n"] for r in rows], color="tab:green", label="best n (n*E)")
    ax_n.bar_label(bars, fontsize=8)
    if any(r["n_tol"] for r in rows):
        ax_n.plot([x for x, r in zip(xs, rows) if r["n_tol"]],
                  [r["n_tol"] for r in rows if r["n_tol"]], "k*", ms=12,
                  label="smallest n for the tolerance")
    ax_n.set(title="Iterations", ylabel="n")
    ax_n.legend(fontsize=8)

    bars = ax_l.bar(xs, [100 * r["les"] / DE1_LES for r in rows], color="tab:purple")
    ax_l.bar_label(bars, labels=[f"~{r['les']} LEs" for r in rows], fontsize=8)
    ax_l.set(title=f"Estimated logic use of the DE1 ({DE1_LES} LEs)", ylabel="% of DE1 LEs")

    for ax in (ax_e, ax_t, ax_n, ax_l):
        ax.set_xticks(xs, labels)
        ax.grid(True, axis="y", which="both", alpha=0.3)
        ax.margins(y=0.15)
    fig.suptitle(f"Hyperbolic CORDIC {func}: datapath width comparison "
                 f"(worst case over t, LE counts estimated)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plotFormats(func: str, table: dict, int_bits: int, tols: list, out_path: Path) -> None:
    """Writes a 1x2 PNG to out_path. Left: worst |error| vs AT cost for every (frac, n),
    the Pareto front, tolerance lines and each tolerance's pick. Right: AT cost of each
    frac at its cheapestN, one line per tolerance, pick starred. Imports matplotlib here.
    Side effect: writes out_path."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax_f, ax_c) = plt.subplots(1, 2, figsize=(16, 7))
    cmap = plt.get_cmap("viridis")
    fracs = sorted(table)
    points = []
    for idx, frac in enumerate(fracs):
        color = cmap(idx / max(1, len(fracs) - 1))
        costs = [atCost(frac, n, int_bits) for n in range(1, len(table[frac]) + 1)]
        ax_f.scatter(costs, table[frac], s=10, color=color, alpha=0.5,
                     label=f"Q{int_bits}.{frac}")
        points += [(c, e, frac, n + 1) for n, (c, e) in enumerate(zip(costs, table[frac]))]
    front = paretoFront(points)
    ax_f.plot([p[0] for p in front], [p[1] for p in front], "k-", lw=1.5,
              label="Pareto front")

    tol_colors = plt.get_cmap("tab10")
    for k, tol in enumerate(tols):
        color = tol_colors(k)
        ax_f.axhline(tol, color=color, ls="--", lw=1)
        pick = pickFormat(table, int_bits, tol)
        if pick is not None:
            frac, n = pick
            cost = atCost(frac, n, int_bits)
            ax_f.plot([cost], [table[frac][n - 1]], "*", ms=16, color=color, mec="k", zorder=5)
            ax_f.annotate(f"Q{int_bits}.{frac} n={n}", (cost, table[frac][n - 1]),
                          textcoords="offset points", xytext=(8, -12), fontsize=9,
                          color=color)
        xs, ys = [], []
        for frac in fracs:
            m = cheapestN(table[frac], tol)
            if m:
                xs.append(frac)
                ys.append(atCost(frac, m, int_bits))
        ax_c.plot(xs, ys, "-o", ms=4, color=color, label=f"max |error| <= {tol:g}")
        if pick is not None:
            ax_c.plot([pick[0]], [atCost(pick[0], pick[1], int_bits)], "*", ms=16,
                      color=color, mec="k", zorder=5)

    ax_f.set_yscale("log")
    ax_f.set(title="Every (frac, n): worst |error| vs cost (dashed = tolerance, star = pick)",
             xlabel="cost = width x cycles  (width = frac + int bits, cycles = n + 1)",
             ylabel="max |error| over t")
    ax_f.legend(fontsize=7, ncol=3, loc="upper right")
    ax_c.set(title="Cheapest cost reaching each tolerance, per format (star = cheapest)",
             xlabel="fraction bits", ylabel="cost = width x cycles at the smallest n")
    ax_c.set_xticks(fracs)
    ax_c.legend()
    for ax in (ax_f, ax_c):
        ax.grid(True, which="both", alpha=0.3)
    fig.suptitle(f"Hyperbolic CORDIC {func}: which fixed-point format is cheapest for a "
                 f"required accuracy ({int_bits} integer bits, worst case over t)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plotSweep(func: str, table: dict, int_bits: int, out_path: Path) -> None:
    """Writes a 2x2 PNG to out_path: worst |error| vs n, n*|error| vs n, error change per
    iteration (in LSB), and both picked n vs frac. Imports matplotlib here so the pure
    functions above work without it. Side effect: writes out_path."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ((ax_e, ax_p), (ax_d, ax_b)) = plt.subplots(2, 2, figsize=(14, 10))
    cmap = plt.get_cmap("viridis")
    fracs = list(table)
    best_p, best_d = [], []
    for idx, frac in enumerate(fracs):
        errs = table[frac]
        lsb = 2.0 ** -frac
        ns = list(range(1, len(errs) + 1))
        color = cmap(idx / max(1, len(fracs) - 1))
        n_p, n_d = bestByProduct(errs), bestByDelta(errs, lsb)
        best_p.append(n_p)
        best_d.append(n_d)
        label = f"frac {frac}"

        ax_e.semilogy(ns, errs, "-o", ms=3, color=color, label=label)
        ax_e.semilogy([n_p], [errs[n_p - 1]], "*", ms=12, color=color, mec="k")

        prod = [n * e for n, e in zip(ns, errs)]
        ax_p.semilogy(ns, prod, "-o", ms=3, color=color, label=label)
        ax_p.semilogy([n_p], [prod[n_p - 1]], "*", ms=12, color=color, mec="k")

        deltas = [d / lsb for d in errorDeltas(errs)]
        ax_d.plot(ns[1:], deltas, "-o", ms=3, color=color, label=label)
        ax_d.plot([n_d], [deltas[n_d - 2] if n_d >= 2 else 0.0], "s", ms=8, color=color,
                  mec="k")

    ax_e.set(title="Worst-case |error| vs iterations (star = argmin n*E)",
             xlabel="iterations n", ylabel="max |error|")
    ax_p.set(title="Cost n * |error| vs iterations (star = minimum)",
             xlabel="iterations n", ylabel="n * max |error|")
    ax_d.set_yscale("symlog", linthresh=1.0)
    ax_d.axhline(1.0, color="r", ls="--", lw=1, label="1 LSB")
    ax_d.axhline(0.0, color="k", lw=0.5)
    ax_d.set(title="Error change per iteration E(n-1) - E(n) (square = dE pick)",
             xlabel="iterations n", ylabel="improvement [LSB] (symlog)")

    ax_b.plot(fracs, best_p, "-*", ms=10, label="argmin n*E")
    ax_b.plot(fracs, best_d, "-s", ms=6, label="no later gain >= 1 LSB")
    ax_b.plot(fracs, [f + 1 for f in fracs], ":", color="gray", label="frac + 1")
    ax_b.set(title="Picked iteration count vs fraction bits",
             xlabel="fraction bits", ylabel="iterations n")
    for ax in (ax_e, ax_p, ax_d, ax_b):
        ax.grid(True, which="both", alpha=0.3)
    for ax in (ax_e, ax_p, ax_d):
        ax.legend(fontsize=7, ncol=2)
    ax_b.legend()
    fig.suptitle(f"Hyperbolic CORDIC {func}: iterations vs error "
                 f"(fixed point, {int_bits} integer bits, worst case over t)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


# === CLI ===

def main(argv: Optional[list] = None) -> int:
    """CLI entry: with --widths runs the width comparison (table + width_compare_<func>.png);
    otherwise runs the frac sweep (tables + two PNGs). Returns the exit code (0 = ok,
    2 = bad arguments via argparse)."""
    p = argparse.ArgumentParser(description="CORDIC iterations vs error sweep.")
    p.add_argument("--func", choices=cordic.FUNCS, default="cosh")
    p.add_argument("--frac-min", type=int, default=6)
    p.add_argument("--frac-max", type=int, default=20)
    p.add_argument("--frac-step", type=int, default=1)
    p.add_argument("--tol", type=float, nargs="+", default=[1e-2, 1e-3, 1e-4, 1e-5],
                   help="required max |error| values for the format choice")
    p.add_argument("--n-max", type=int, default=30, help="highest iteration count (default 30)")
    p.add_argument("--int-bits", type=int, default=2,
                   help="integer bits incl. sign; width = frac + int_bits (default 2 = Q2.f)")
    p.add_argument("--points", type=int, default=101, help="t grid size (default 101)")
    p.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent,
                   help="folder for the PNGs (default: next to this file)")
    p.add_argument("--widths", type=int, nargs="+", default=None,
                   help="compare these total widths instead of the frac sweep, e.g. "
                        "--widths 8 12 16 24 32 (uses the first --tol)")
    p.add_argument("--clock-mhz", type=float, default=DE1_CLOCK_HZ / 1e6,
                   help="FPGA clock for the time estimate (default 50 = DE1 CLOCK_50)")
    p.add_argument("--baud", type=float, default=9600,
                   help="UART baud rate for the transfer time (default 9600)")
    a = p.parse_args(argv)
    if a.frac_min < 1 or a.frac_max < a.frac_min or a.frac_step < 1 or a.n_max < 2 \
            or a.int_bits < 1 or not all(math.isfinite(t) and t > 0 for t in a.tol) \
            or a.clock_mhz <= 0 or a.baud <= 0:
        p.error("need 1 <= frac-min <= frac-max, frac-step >= 1, n-max >= 2, int-bits >= 1,"
                " every tol > 0, clock-mhz > 0, baud > 0")

    if a.widths is not None:
        if any(w <= a.int_bits for w in a.widths):
            p.error("every width must be larger than --int-bits")
        ts = tGrid(a.func, a.points)
        n_max = max(a.n_max, max(a.widths) + 6)   # best n is about width, leave headroom
        rows = [widthSummary(a.func, w, a.int_bits, ts, n_max, a.clock_mhz * 1e6, a.baud,
                             a.tol[0]) for w in a.widths]
        print(formatWidths(a.func, rows, a.int_bits, a.tol[0], a.clock_mhz * 1e6, a.baud))
        png = a.out_dir / f"width_compare_{a.func}.png"
        plotWidths(a.func, rows, a.int_bits, png)
        print(f"\nplot written to {png}")
        return 0

    fracs = list(range(a.frac_min, a.frac_max + 1, a.frac_step))
    ts = tGrid(a.func, a.points)
    table = errorTable(a.func, fracs, a.n_max, a.int_bits, ts)
    print(formatTable(a.func, table, a.int_bits))
    print()
    print(formatChoice(table, a.int_bits, a.tol))

    sweep_png = a.out_dir / f"iterative_vs_error_{a.func}.png"
    choice_png = a.out_dir / f"format_choice_{a.func}.png"
    # every other frac only: one line per frac is unreadable at step 1
    plotSweep(a.func, {f: e for f, e in table.items() if (f - a.frac_min) % 2 == 0},
              a.int_bits, sweep_png)
    plotFormats(a.func, table, a.int_bits, a.tol, choice_png)
    print(f"\nplots written to {sweep_png} and {choice_png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
