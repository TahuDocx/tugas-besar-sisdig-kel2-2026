// Hyperbolic CORDIC core. Pure logic, runs in browser (window.Cordic) and Node (require).
// Fixed-point mode is bit-exact integer math: what your Verilog/VHDL datapath should produce.
(function (root) {
  'use strict';

  // Shift indices i = 1,2,3,4,4,5,...,13,13,...,40,40,...  (repeat 4, 13, 40, ... k -> 3k+1)
  // Without repeats hyperbolic CORDIC does NOT converge.
  // repeats = false gives plain 1..n: only for demonstrating why repeats are needed.
  function schedule(n, repeats = true) {
    const out = [];
    let rep = 4;
    for (let i = 1; out.length < n; i++) {
      out.push(i);
      if (repeats && i === rep && out.length < n) { out.push(i); rep = 3 * rep + 1; }
    }
    return out;
  }

  // K = prod sqrt(1 - 2^-2i) over the schedule (~0.82816). Rotation mode starts at x0 = 1/K to cancel it.
  const gain = (sched) => sched.reduce((k, i) => k * Math.sqrt(1 - Math.pow(2, -2 * i)), 1);

  // Verilog `>>>` on signed regs = floor division by 2^s.
  const ashr = (v, s) => Math.floor(v / Math.pow(2, s));

  // Two's-complement wrap to `width` bits (what a register of that width does on overflow).
  function wrap(v, width) {
    const m = Math.pow(2, width), h = m / 2;
    return ((((v + h) % m) + m) % m) - h;
  }

  // mode: 'rotation' (drive z -> 0) or 'vectoring' (drive y -> 0).
  // fixed = { frac, width } for integer datapath, or null for float.
  function run(mode, x0, y0, z0, n, fixed) {
    const sched = schedule(n);
    const scale = fixed ? Math.pow(2, fixed.frac) : 1;
    let overflow = false;
    const q = (v) => {
      if (!fixed) return v;
      const w = wrap(v, fixed.width);
      if (w !== v) overflow = true;
      return w;
    };
    const load = (v) => (fixed ? q(Math.round(v * scale)) : v);
    const shr = (v, s) => (fixed ? ashr(v, s) : v * Math.pow(2, -s));

    const lut = sched.map((i) => load(Math.atanh(Math.pow(2, -i))));
    let x = load(x0), y = load(y0), z = load(z0);
    const steps = [{ k: 0, i: null, d: null, x, y, z }];

    sched.forEach((i, k) => {
      const d = mode === 'rotation' ? (z >= 0 ? 1 : -1) : (y < 0 ? 1 : -1);
      const xs = shr(x, i), ys = shr(y, i);
      const nx = q(x + d * ys);
      const ny = q(y + d * xs);
      const nz = q(z - d * lut[k]);
      x = nx; y = ny; z = nz;
      steps.push({ k: k + 1, i, d, x, y, z, xs, ys, a: lut[k] });
    });

    return { mode, sched, lut, steps, scale, K: gain(sched), overflow, fixed };
  }

  // Domain limits come from sum of atanh table (~1.1182 for any useful n).
  const thetaMax = (n) => schedule(n).reduce((s, i) => s + Math.atanh(Math.pow(2, -i)), 0);

  // func -> setup + how to read result. Returns { value, expected, run, inRange }.
  function compute(func, t, opts) {
    const n = opts.n, fixed = opts.frac != null ? { frac: opts.frac, width: opts.width } : null;
    const K = gain(schedule(n));
    const tm = thetaMax(n), rMax = Math.tanh(tm);
    let r, value, expected, inRange;
    const last = () => r.steps[r.steps.length - 1];
    const real = (v) => v / r.scale;

    switch (func) {
      case 'cosh': case 'sinh': case 'exp':
        r = run('rotation', 1 / K, 0, t, n, fixed);
        inRange = Math.abs(t) <= tm;
        value = func === 'cosh' ? real(last().x) : func === 'sinh' ? real(last().y) : real(last().x + last().y);
        expected = Math[func](t);
        break;
      case 'atanh':
        r = run('vectoring', 1, t, 0, n, fixed);
        inRange = Math.abs(t) <= rMax;
        value = real(last().z);
        expected = Math.atanh(t);
        break;
      case 'ln': // ln w = 2 * atanh((w-1)/(w+1))
        r = run('vectoring', t + 1, t - 1, 0, n, fixed);
        inRange = t > 0 && Math.abs((t - 1) / (t + 1)) <= rMax;
        value = 2 * real(last().z);
        expected = Math.log(t);
        break;
      case 'sqrt': { // sqrt w = sqrt((w+1/4)^2 - (w-1/4)^2); vectoring gives K*sqrt(...) so multiply by 1/K
        r = run('vectoring', t + 0.25, t - 0.25, 0, n, fixed);
        inRange = t > 0 && Math.abs((t - 0.25) / (t + 0.25)) <= rMax;
        const xn = last().x;
        value = fixed ? real(ashr(xn * Math.round(r.scale / K), fixed.frac)) : xn / K;
        expected = Math.sqrt(t);
        break;
      }
      default: throw new Error('unknown func ' + func);
    }
    return { value, expected, run: r, inRange, K, thetaMax: tm, ratioMax: rMax };
  }

  const api = { schedule, gain, ashr, wrap, run, compute, thetaMax };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Cordic = api;
})(this);
