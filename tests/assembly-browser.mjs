import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
const browser = await chromium.launch({ headless: true, channel: "msedge" });
const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
try {
  await page.goto("http://127.0.0.1:5173");
  await page.waitForFunction(() => window.__actuator);
  const originalColors = await page.evaluate(() =>
    window.__actuator.meshes.map((m) => m.material.color.getHex()),
  );
  await page.click("#assembly-guide");
  assert.equal(await page.locator("#assembly-step option").count(), 30);
  const coverage = await page.evaluate(async () => {
    const a = window.__actuator,
      d = await (await fetch("data/assembly-sequence.json")).json();
    const ids = d.steps.flatMap((s) => s.parts);
    return {
      missing: a.bom
        .filter(
          (b) => !ids.some((id) => id === b.id || id.startsWith(b.id + "/")),
        )
        .map((b) => b.id),
      invalid: [
        ...new Set(d.steps.flatMap((s) => [...s.parts, ...s.target])),
      ].filter((id) => !a.assembly.nodes.has(id)),
    };
  });
  assert.deepEqual(coverage, { missing: [], invalid: [] });
  await page.selectOption("#assembly-step", "4");
  await page.locator("#assembly-progress").fill("100");
  assert.match(
    await page.locator("#assembly-detail").innerText(),
    /68 individual/,
  );
  assert.ok(
    (await page.evaluate(
      () =>
        window.__actuator.meshes.filter(
          (m) => m.visible && m.userData.nodeId.startsWith("EM01/"),
        ).length,
    )) >= 68,
  );
  await page.screenshot({ path: "tmp/qa/assembly-guide.png", fullPage: true });
  await page.selectOption("#assembly-step", "8");
  await page.selectOption("#assembly-speed", "2");
  await page.click("#assembly-play");
  await page.waitForFunction(
    () => window.__actuator.assemblyGuide.getState().index === 9,
  );
  assert.equal(
    await page.evaluate(
      () => window.__actuator.assemblyGuide.getState().playing,
    ),
    false,
  );
  assert.match(await page.locator("#assembly-detail").innerText(), /Blocked/);
  await page.click("#assembly-next");
  await page.click("#assembly-prev");
  await page.locator("#assembly-progress").fill("45");
  await page.click("#assembly-close");
  assert.equal(await page.locator("#assembly-panel").isVisible(), false);
  assert.equal(
    await page.evaluate(() =>
      window.__actuator.meshes.every(
        (m) => m.position.distanceTo(m.userData.basePosition) < 1e-9,
      ),
    ),
    true,
  );
  await page.click("#assembly-guide");
  await page.selectOption("#assembly-step", "4");
  await page.locator('#assembly-detail [data-mate="EM01"]').click();
  assert.equal(
    await page.evaluate(
      () => window.__actuator.assemblyGuide.getState().active,
    ),
    true,
  );
  await page.click("#assembly-close");
  assert.deepEqual(
    await page.evaluate(() =>
      window.__actuator.meshes.map((m) => m.material.color.getHex()),
    ),
    originalColors,
  );
  assert.deepEqual(errors, []);
  console.log(
    "Assembly guide: BOM coverage, node references, lamination playback, blocked-step pause, controls, exit restoration pass.",
  );
} finally {
  await browser.close();
}
