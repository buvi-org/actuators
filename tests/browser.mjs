import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
const browser = await chromium.launch({
  headless: true,
  channel: process.env.BROWSER_CHANNEL || "msedge",
});
const page = await browser.newPage({
  viewport: { width: 1440, height: 1120 },
  deviceScaleFactor: 1,
});
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const url = process.env.TEST_URL || "http://127.0.0.1:5173";
await fs.mkdir("tmp/qa", { recursive: true });
try {
  await page.goto(url);
  await page.waitForFunction(() => window.__actuator);
  const meshCount = await page.evaluate(() => window.__actuator.meshes.length);
  assert.ok(meshCount > 380);
  // The full-assembly export writes every mesh the viewer holds.
  assert.equal(
    await page.evaluate(
      () => window.__actuator.meshes.filter((m) => m.geometry).length,
    ),
    meshCount,
  );
  // 42 source occurrences minus G02 and G03: the sun blank and the rotor hub are both
  // replaced by study solids, so their source meshes are not linked as reference geometry.
  assert.equal(
    await page.evaluate(
      () =>
        window.__actuator.meshes.filter(
          (m) => m.userData.geometryKind === "reference",
        ).length,
    ),
    41,
  );
  assert.equal(
    await page.evaluate(() =>
      window.__actuator.meshes.filter((m) =>
        ["G02/NAUO41", "G03/NAUO45"].includes(m.userData.nodeId),
      ).length,
    ),
    0,
  );
  assert.ok(
    await page.evaluate(() =>
      window.__actuator.bom.every((row) =>
        window.__actuator.assembly.nodes.has(row.id),
      ),
    ),
  );
  // Interpenetration is checked exactly, on the solids, by cad/check_intersections.py,
  // which npm test runs first. A viewer-side bounding-box test would be too coarse to
  // mean anything: adjacent curved bodies always overlap as boxes.
  await page.evaluate(() => window.__actuator.selectPart("M01"));
  assert.match(
    await page.locator("#component-detail").innerText(),
    /stator seat stays at its Choice C position/,
  );
  // The housing inspector must still disclose the unresolved rotor clearance.
  assert.match(
    await page.locator("#component-detail").innerText(),
    /rotor-clearance redesign/,
  );
  // Every selected part carries a dimensioned section diagram, measured from the mesh.
  assert.equal(
    await page.locator("#component-detail .section-fig svg").count(),
    1,
  );
  assert.equal(
    await page
      .locator('a[download][href$="main-housing-supported.step"]')
      .count(),
    1,
  );
  await page.locator("#isolate-part").click();
  assert.equal(
    await page.evaluate(
      () => window.__actuator.meshes.filter((m) => m.visible).length,
    ),
    2,
  );
  await page.evaluate(() =>
    window.__actuator.toggleVisibility("M01/boss-extensions"),
  );
  assert.equal(
    await page.evaluate(
      () => window.__actuator.meshes.filter((m) => m.visible).length,
    ),
    1,
  );
  await page.locator("#all-parts").click();
  assert.equal(
    await page.evaluate(
      () => window.__actuator.assembly.nodes.get("G05").children.length,
    ),
    0,
  );
  assert.equal(
    await page.evaluate(
      () =>
        window.__actuator.meshes.filter((m) => m.userData.nodeId === "G05")
          .length,
    ),
    1,
  );
  await page.locator("#mounting-view").click();
  assert.equal(
    await page.evaluate(
      () =>
        window.__actuator.meshes.filter(
          (m) => m.visible && m.userData.nodeId.startsWith("F01/"),
        ).length,
    ),
    8,
  );
  assert.equal(
    await page.evaluate(() => window.__actuator.getState().selected),
    "G05",
  );
  await page.screenshot({ path: "tmp/qa/stator-mount.png", fullPage: true });
  await page.evaluate(() => window.__actuator.selectPart("F01/NAUO24"));
  assert.match(
    await page.locator("#component-detail").innerText(),
    /Front joint: main housing/,
  );
  await page.locator("#gear-view").click();
  assert.equal(
    await page.evaluate(() => window.__actuator.getState().selected),
    "G02",
  );
  assert.ok(
    await page
      .locator("#component-detail")
      .innerText()
      .then(
        (t) => t.includes("20-tooth") && t.toLowerCase().includes("involute"),
      ),
  );
  await page.screenshot({ path: "tmp/qa/gear-train.png", fullPage: true });
  await page.locator("#internal-view").click();
  await page.evaluate(() => window.__actuator.selectPart("EM04"));
  await page.locator("#isolate-part").click();
  // 42 magnet segments plus the retaining ring that captures them.
  assert.equal(
    await page.evaluate(
      () => window.__actuator.meshes.filter((m) => m.visible).length,
    ),
    43,
  );
  await page.locator("#all-parts").click();
  await page.evaluate(() => window.__actuator.selectPart("EM01/L001"));
  await page.locator("#hide-part").click();
  assert.equal(
    await page.evaluate(
      () => window.__actuator.meshes.filter((m) => m.visible).length,
    ),
    meshCount - 1,
  );
  assert.equal(
    await page
      .locator('[data-visible="EM01"]')
      .evaluate((e) => e.indeterminate),
    true,
  );
  await page.locator("#all-parts").click();
  await page.evaluate(() => window.__actuator.selectPart("pcb:R6"));
  assert.match(
    await page.locator("#component-detail").innerText(),
    /Package model labels/,
  );
  assert.equal(await page.locator("#isolate-part").isDisabled(), true);
  await page.locator("#internal-view").click();
  await page.screenshot({ path: "tmp/qa/assembly.png", fullPage: true });
  await page.locator("#exploded").click();
  assert.equal(
    await page.evaluate(() => window.__actuator.getState().separation),
    0.65,
  );
  await page.screenshot({ path: "tmp/qa/exploded.png", fullPage: true });
  await page.locator('[data-id="G02"]').click();
  await page.locator("#isolate-part").click();
  assert.equal(
    await page.evaluate(
      () => window.__actuator.meshes.filter((m) => m.visible).length,
    ),
    1,
  );
  await page.locator("#all-parts").click();
  assert.equal(
    await page.evaluate(
      () => window.__actuator.meshes.filter((m) => m.visible).length,
    ),
    meshCount,
  );
  const [assemblyDownload] = await Promise.all([
    page.waitForEvent("download"),
    page.locator("#export-assembly").click(),
  ]);
  await assemblyDownload.saveAs("tmp/qa/complete-assembly.glb");
  const assemblyBytes = await fs.readFile("tmp/qa/complete-assembly.glb");
  const assemblyGltf = JSON.parse(
    assemblyBytes.toString("utf8", 20, 20 + assemblyBytes.readUInt32LE(12)),
  );
  assert.equal(
    assemblyGltf.nodes.filter((n) => n.mesh !== undefined).length,
    meshCount,
  );
  assert.ok(assemblyGltf.nodes.some((n) => n.extras?.id === "G02"));
  await page.locator("#section").click();
  assert.equal(
    await page.evaluate(() => window.__actuator.getState().section),
    true,
  );
  await page.locator('[data-tab="bom"]').click();
  await page.locator("#bom-search").fill("6701");
  const bearingHits = await page
    .locator("#bom-body tr")
    .evaluateAll((rows) =>
      rows.map((r) => [r.querySelector(".id").innerText, r.innerText.toLowerCase()]),
    );
  // The 6701-ZZ row must be found, and every hit must actually mention it. A broad
  // query may also match a record that names the bearing as a mating part.
  assert.ok(bearingHits.some(([id]) => id.startsWith("B03")));
  assert.ok(bearingHits.length >= 1);
  assert.ok(bearingHits.every(([, text]) => text.includes("6701")));
  await page.locator("#driver-search").fill("LQFP64");
  assert.ok((await page.locator("#driver-body tr").count()) > 0);
  await page.locator('[data-tab="lamination"]').click();
  await page.waitForFunction(() => window.__lamination);
  let state = await page.evaluate(() => window.__lamination.getState());
  assert.equal(state.result.count, 68);
  await page.screenshot({ path: "tmp/qa/lamination.png", fullPage: true });
  await page.locator("#lam-coating").fill("5");
  await page.locator("#lam-coating").press("Tab");
  state = await page.evaluate(() => window.__lamination.getState());
  assert.equal(state.result.count, 66);
  await page.locator("#lam-spread").fill("40");
  await page.locator("#lam-spread").dispatchEvent("change");
  await page.screenshot({
    path: "tmp/qa/lamination-spread.png",
    fullPage: true,
  });
  await page.locator("#lam-view-mode").selectOption("single");
  assert.equal(
    await page.evaluate(() => window.__lamination.getState().viewMode),
    "single",
  );
  await page.locator("#lam-reset").click();
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.locator("#lam-export-json").click(),
  ]);
  await download.saveAs("tmp/qa/lamination-study.json");
  const study = JSON.parse(await fs.readFile("tmp/qa/lamination-study.json"));
  assert.equal(study.results.count, 68);
  assert.equal(study.manufacturerProfile, false);
  const [glbDownload] = await Promise.all([
    page.waitForEvent("download"),
    page.locator("#lam-export-glb").click(),
  ]);
  await glbDownload.saveAs("tmp/qa/lamination-stack.glb");
  const glb = await fs.readFile("tmp/qa/lamination-stack.glb");
  assert.equal(glb.toString("utf8", 0, 4), "glTF");
  const gltf = JSON.parse(glb.toString("utf8", 20, 20 + glb.readUInt32LE(12)));
  assert.equal(gltf.nodes.filter((n) => n.mesh !== undefined).length, 204);
  await page.locator("#lam-steel").fill("0");
  await page.locator("#lam-steel").press("Tab");
  assert.equal(await page.locator("#lam-error").isVisible(), true);
  assert.equal(await page.locator("#lam-export-json").isDisabled(), true);
  await page.locator("#lam-reset").click();
  assert.equal(await page.locator("#lam-error").isVisible(), false);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(
    () => (document.querySelector(".lam-controls").scrollTop = 0),
  );
  await page.evaluate(
    () =>
      new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)),
      ),
  );
  await page.screenshot({
    path: "tmp/qa/mobile-lamination.png",
    fullPage: true,
  });
  assert.ok(
    await page.evaluate(() => document.body.scrollWidth <= innerWidth + 1),
    "mobile lamination horizontal overflow",
  );
  await page.locator('[data-tab="model"]').click();
  await page.locator("#assembled").click();
  await page.screenshot({ path: "tmp/qa/mobile-assembly.png", fullPage: true });
  assert.ok(
    await page.evaluate(() => document.body.scrollWidth <= innerWidth + 1),
    "mobile assembly horizontal overflow",
  );
  assert.deepEqual(errors, []);
  console.log(
    "Browser checks passed: CAD loading, explode/section/isolate, BOM search, layer sizing, invalid inputs, JSON/GLB export, desktop/mobile layout.",
  );
} finally {
  await browser.close();
}
