// Generates golden.json from the JS reference (cordic-sim/cordic.js).
// Run from repo root: node cordic-sim-py/golden/gen_golden.js
// The Python port must reproduce every step of these runs bit-exactly.
const fs = require('fs');
const path = require('path');
const C = require('../../cordic-sim/cordic.js');

const cases = [];
const funcs = {
  cosh: [-1.1, -0.3, 0, 0.5, 1.0],
  sinh: [-0.8, 0.25, 1.1],
  exp: [-1, 0.7],
  atanh: [-0.6, 0.5, 0.8],
  ln: [0.2, 1, 2, 5],
  sqrt: [0.1, 0.5, 1, 2],
};
const formats = [
  { n: 16, frac: 14, width: 16 }, // DE1 target: 1 sign, 1 integer, 14 fraction
  { n: 16, frac: 16, width: 24 },
  { n: 12, frac: 14, width: 16 },
  { n: 24 }, // float
];

for (const [func, ts] of Object.entries(funcs)) {
  for (const t of ts) {
    for (const opts of formats) {
      const r = C.compute(func, t, opts);
      cases.push({
        func, t, opts,
        value: r.value, expected: r.expected, inRange: r.inRange,
        K: r.K, thetaMax: r.thetaMax, ratioMax: r.ratioMax,
        run: { mode: r.run.mode, sched: r.run.sched, lut: r.run.lut, steps: r.run.steps,
               scale: r.run.scale, overflow: r.run.overflow },
      });
    }
  }
}
// Overflow case from cordic.test.js.
const o = C.compute('sqrt', 9, { n: 12, frac: 14, width: 16 });
cases.push({ func: 'sqrt', t: 9, opts: { n: 12, frac: 14, width: 16 }, value: o.value,
  expected: o.expected, inRange: o.inRange, K: o.K, thetaMax: o.thetaMax, ratioMax: o.ratioMax,
  run: { mode: o.run.mode, sched: o.run.sched, lut: o.run.lut, steps: o.run.steps,
         scale: o.run.scale, overflow: o.run.overflow } });

fs.writeFileSync(path.join(__dirname, 'golden.json'), JSON.stringify(cases, null, 1));
console.log(`wrote ${cases.length} cases`);
