// Run: node --test cordic-sim/cordic.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const C = require('./cordic.js');

const near = (a, b, tol) => assert.ok(Math.abs(a - b) <= tol, `${a} vs ${b} (tol ${tol})`);

test('schedule repeats shifts 4, 13, 40', () => {
  assert.deepEqual(C.schedule(6), [1, 2, 3, 4, 4, 5]);
  const s = C.schedule(16);
  assert.equal(s.length, 16);
  assert.deepEqual(s.filter((v) => v === 13), [13, 13]);
});

test('schedule without repeats is plain 1..n (for the "why repeat" demo)', () => {
  assert.deepEqual(C.schedule(6, false), [1, 2, 3, 4, 5, 6]);
});

test('without repeats some angles are unreachable: t = 0.55 gets stuck', () => {
  const zEnd = (sched, t) => sched.reduce((z, i) => z - (z >= 0 ? 1 : -1) * Math.atanh(2 ** -i), t);
  assert.ok(Math.abs(zEnd(C.schedule(16, false), 0.55)) > 1e-3);
  assert.ok(Math.abs(zEnd(C.schedule(17), 0.55)) < 1e-4);
});

test('hyperbolic gain converges to ~0.82816', () => {
  near(C.gain(C.schedule(30)), 0.8281593609602, 1e-9);
});

test('arithmetic shift floors negatives like Verilog >>>', () => {
  assert.equal(C.ashr(-5, 1), -3);
  assert.equal(C.ashr(5, 1), 2);
});

test("wrap emulates two's-complement overflow", () => {
  assert.equal(C.wrap(32768, 16), -32768);
  assert.equal(C.wrap(-32769, 16), 32767);
  assert.equal(C.wrap(123, 16), 123);
});

test('float: cosh/sinh/exp', () => {
  for (const t of [-1, -0.3, 0, 0.5, 1.1]) {
    near(C.compute('cosh', t, { n: 24 }).value, Math.cosh(t), 1e-6);
    near(C.compute('sinh', t, { n: 24 }).value, Math.sinh(t), 1e-6);
    near(C.compute('exp', t, { n: 24 }).value, Math.exp(t), 1e-6);
  }
});

test('float: atanh/ln/sqrt (vectoring)', () => {
  near(C.compute('atanh', 0.5, { n: 24 }).value, Math.atanh(0.5), 1e-6);
  for (const w of [0.2, 1, 2, 5]) near(C.compute('ln', w, { n: 24 }).value, Math.log(w), 1e-5);
  for (const w of [0.1, 1, 2]) near(C.compute('sqrt', w, { n: 24 }).value, Math.sqrt(w), 1e-5);
});

test('out-of-domain inputs flagged (no convergence)', () => {
  assert.equal(C.compute('sqrt', 5, { n: 24 }).inRange, false);
  assert.equal(C.compute('cosh', 2, { n: 24 }).inRange, false);
  assert.equal(C.compute('cosh', 1, { n: 24 }).inRange, true);
});

test('fixed Q.16: integer datapath, result within quantization error', () => {
  const o = { n: 16, frac: 16, width: 24 };
  near(C.compute('cosh', 0.5, o).value, Math.cosh(0.5), 5e-4);
  near(C.compute('sinh', -0.8, o).value, Math.sinh(-0.8), 5e-4);
  near(C.compute('ln', 2, o).value, Math.log(2), 5e-4);
  const r = C.compute('cosh', 0.5, o).run;
  for (const s of r.steps) assert.ok(Number.isInteger(s.x) && Number.isInteger(s.y) && Number.isInteger(s.z));
  assert.ok(r.lut.every(Number.isInteger));
  assert.equal(r.overflow, false);
});

test('fixed overflow is flagged', () => {
  // sqrt(9): x0 = 9.25 -> 9.25 * 2^14 > 2^15 - 1 in a 16-bit word
  assert.equal(C.compute('sqrt', 9, { n: 12, frac: 14, width: 16 }).run.overflow, true);
});
