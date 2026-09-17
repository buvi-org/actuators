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
  assert.equal(await page.evaluate(() => window.__actuator.meshes.length), 43);
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
    43,
  );
  await page.locator("#section").click();
  assert.equal(
    await page.evaluate(() => window.__actuator.getState().section),
    true,
  );
  await page.locator('[data-tab="bom"]').click();
  await page.locator("#bom-search").fill("6701");
  assert.equal(await page.locator("#bom-body tr").count(), 1);
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
