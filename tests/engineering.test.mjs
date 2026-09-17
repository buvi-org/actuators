import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import {
  defaults,
  calculateStack,
  profilePoints,
  profileDXF,
} from "../src/lamination-math.js";
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-8, `${a} != ${b}`);
test("two coating faces per sheet, all exterior faces included", () => {
  const r = calculateStack(defaults);
  assert.equal(r.count, 68);
  near(r.gross, 13.872);
  near(r.iron, 13.6);
  near(r.coatingTotal, 0.272);
  near(r.remaining, 0.128);
  near(r.fillFactor, 13.6 / 13.872);
});
test("zero coating allows 70 sheets without floating point off-by-one", () => {
  const r = calculateStack({ ...defaults, coating: 0, coatingTolerance: 0 });
  assert.equal(r.count, 70);
  near(r.gross, 14);
});
test("additional interface gap occurs N-1 times; end allowance occurs once", () => {
  const r = calculateStack({
    ...defaults,
    mode: "count",
    count: 3,
    gap: 10,
    endAllowance: 0.5,
  });
  near(r.gross, 0.632);
  near(r.total, 1.132);
  near(r.gapTotal, 0.02);
  const single = calculateStack({
    ...defaults,
    mode: "count",
    count: 1,
    gap: 100,
  });
  near(single.gross, 0.204);
  near(single.gapTotal, 0);
});
test("conservative count uses upper bounds of all tolerances", () => {
  const r = calculateStack(defaults);
  assert.equal(r.conservativeCount, 66);
  near(r.worstMax, 14.28);
  assert.equal(r.worstFits, false);
  const safe = calculateStack({
    ...defaults,
    mode: "count",
    count: r.conservativeCount,
  });
  assert.equal(safe.worstFits, true);
});
test("fixed count may exceed budget and reports it explicitly", () => {
  const r = calculateStack({ ...defaults, mode: "count", count: 70 });
  assert.equal(r.fits, false);
  near(r.remaining, -0.28);
});
test("increasing coating never increases sheet count", () => {
  let last = Infinity;
  for (let coating = 0; coating <= 100; coating += 0.5) {
    const r = calculateStack({ ...defaults, coating });
    assert.ok(r.count <= last);
    assert.ok(r.gross <= defaults.budget + 1e-8);
    last = r.count;
  }
});
test("comparison calculation is not limited by the 3D sheet-rendering cap", () => {
  const p = { ...defaults, steel: 0.05, steelTolerance: 0.001, budget: 26 };
  assert.equal(calculateStack({ ...p, coating: 0 }).count, 520);
  assert.equal(calculateStack(p).count, 481);
});
test("invalid geometry and numerical values fail instead of producing plausible output", () => {
  for (const patch of [
    { coating: -1 },
    { steel: NaN },
    { count: 3.5 },
    { bore: 90 },
    { rootDiameter: 51 },
    { tipWidth: 100 },
    { steelTolerance: 0.2 },
    { endAllowance: 14 },
    { mode: "unknown" },
  ])
    assert.throws(() => calculateStack({ ...defaults, ...patch }));
});
test("profile has 36 outward teeth and correct exterior diameter", () => {
  const points = profilePoints(defaults);
  assert.equal(points.length, 36 * 12);
  near(Math.max(...points.map(([x, y]) => Math.hypot(x, y))), 40);
  near(Math.min(...points.map(([x, y]) => Math.hypot(x, y))), 31);
  assert.ok(profileDXF(defaults).includes("$INSUNITS\n70\n4"));
  assert.ok(profileDXF(defaults).includes("PROVISIONAL_STEEL"));
});
const manifest = JSON.parse(fs.readFileSync("public/models/manifest.json"));
const bom = JSON.parse(fs.readFileSync("public/data/bom.json"));
test("BOM exactly reconciles all reference CAD instances", () => {
  assert.equal(manifest.parts.length, 43);
  assert.equal(
    manifest.parts.reduce((n, p) => n + p.solids, 0),
    54,
  );
  assert.equal(new Set(manifest.parts.map((p) => p.id)).size, 43);
  for (const row of bom.filter((r) => r.instances.length))
    assert.equal(
      row.quantity,
      manifest.parts.filter((p) => p.bomId === row.id).length,
    );
  assert.equal(
    bom.reduce((sum, r) => sum + r.instances.length, 0),
    43,
  );
  for (const part of manifest.parts)
    assert.ok(
      bom.find((row) => row.id === part.bomId)?.instances.includes(part.id),
    );
});
test("unknown procurement data is retained and driver child lines are identified", () => {
  for (const row of bom) {
    assert.equal(row.unitCost, null);
    assert.equal(row.procurementReady, false);
    if (row.parent) assert.ok(bom.find((p) => p.id === row.parent));
  }
  assert.equal(
    bom.find((r) => r.id === "G04").status,
    "Illustration inference",
  );
  assert.equal(bom.find((r) => r.id === "G06").quantity, null);
});
test("GLB has named geometry for each source occurrence", () => {
  const buffer = fs.readFileSync("public/models/ak80-9-reference.glb");
  assert.equal(buffer.toString("utf8", 0, 4), "glTF");
  assert.equal(buffer.readUInt32LE(4), 2);
  const length = buffer.readUInt32LE(12),
    gltf = JSON.parse(buffer.toString("utf8", 20, 20 + length));
  for (const part of manifest.parts)
    assert.ok(
      gltf.nodes.find((n) => n.name === part.id && n.mesh !== undefined),
      part.id,
    );
});
test("driver inventory preserves 205 unique designators with unknown values", () => {
  const inventory = JSON.parse(
    fs.readFileSync("public/data/driver-inventory.json"),
  );
  assert.equal(inventory.components.length, 205);
  assert.equal(new Set(inventory.components.map((r) => r.reference)).size, 205);
  for (const r of inventory.components) {
    assert.equal(r.value, null);
    assert.equal(r.manufacturerPartNumber, null);
    assert.equal(r.parent, "E01");
    assert.equal(r.quantity, 1);
  }
});
