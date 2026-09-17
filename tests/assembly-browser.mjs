import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
const browser = await chromium.launch({
  headless: true,
  channel: process.env.BROWSER_CHANNEL || "msedge",
});
const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
try {
  await page.goto(process.env.TEST_URL || "http://127.0.0.1:5173");
  await page.waitForFunction(() => window.__actuator);
  const original = await page.evaluate(() =>
    window.__actuator.meshes.map((m) => ({
      color: m.material.color.getHex(),
      opacity: m.material.opacity,
      transparent: m.material.transparent,
      depthWrite: m.material.depthWrite,
    })),
  );
  await page
    .getByRole("button", { name: "Assembly process", exact: true })
    .click();
  assert.equal(await page.locator("#assembly-step option").count(), 20);
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
        ...new Set(
          d.steps.flatMap((s) => [...s.parts, ...s.target, ...s.context]),
        ),
      ].filter((id) => !a.assembly.nodes.has(id)),
    };
  });
  assert.deepEqual(coverage, { missing: [], invalid: [] });
  const visible = () =>
    page.evaluate(() =>
      window.__actuator.meshes
        .filter((m) => m.visible)
        .map((m) => m.userData.nodeId),
    );
  assert.ok((await visible()).every((id) => id.startsWith("M01/")));
  await page.click("#assembly-next");
  assert.match(await page.locator("#assembly-detail").innerText(), /Seat ring/);
  await page.click("#assembly-before");
  assert.ok(!(await visible()).includes("G05"));
  await page.click("#assembly-after");
  assert.ok((await visible()).includes("G05"));
  await page.click("#assembly-next");
  assert.equal(
    (await visible()).filter((id) => id.startsWith("F01/")).length,
    8,
  );
  await page.click("#assembly-next");
  assert.match(
    await page.locator("#assembly-detail").innerText(),
    /68 individual/,
  );
  assert.ok(
    (await visible()).filter((id) => id.startsWith("EM01/")).length >= 68,
  );
  assert.ok(!(await visible()).some((id) => id.startsWith("M02/")));
  await page.check("#assembly-context");
  assert.ok((await visible()).some((id) => id.startsWith("M01/")));
  await page.uncheck("#assembly-context");
  assert.ok(!(await visible()).some((id) => id.startsWith("M01/")));
  await page.check("#assembly-context");
  await page.check("#assembly-cut");
  await fs.mkdir("tmp/qa", { recursive: true });
  await page.screenshot({
    path: "tmp/qa/assembly-process.png",
    fullPage: true,
  });
  for (let i = 0; i < 20; i++) {
    await page.selectOption("#assembly-step", String(i));
    assert.equal(
      await page.evaluate(() =>
        window.__actuator.meshes
          .filter((m) => m.visible)
          .every(
            (m) =>
              m.material.opacity === 1 &&
              !m.material.transparent &&
              m.material.depthWrite,
          ),
      ),
      true,
    );
    assert.equal(
      await page.evaluate(() =>
        window.__actuator.meshes.every(
          (m) => m.position.distanceTo(m.userData.basePosition) < 1e-9,
        ),
      ),
      true,
    );
  }
  // Pauses on entering the first known housing/rotor conflict, without previewing penetration.
  await page.selectOption("#assembly-step", "5");
  await page.click("#assembly-play");
  await page.waitForFunction(
    () => window.__actuator.assemblyGuide.getState().index === 6,
  );
  assert.equal(
    await page.evaluate(
      () => window.__actuator.assemblyGuide.getState().playing,
    ),
    false,
  );
  assert.equal(
    await page.evaluate(
      () => window.__actuator.assemblyGuide.getState().seated,
    ),
    false,
  );
  assert.match(
    await page.locator("#assembly-detail").innerText(),
    /Blocked by known geometry/,
  );
  await page.click("#assembly-prev");
  assert.equal(
    await page.evaluate(() => window.__actuator.assemblyGuide.getState().index),
    5,
  );
  await page.selectOption("#assembly-step", "3");
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
      window.__actuator.meshes.map((m) => ({
        color: m.material.color.getHex(),
        opacity: m.material.opacity,
        transparent: m.material.transparent,
        depthWrite: m.material.depthWrite,
      })),
    ),
    original,
  );
  await page.click("#assembly-guide");
  await page.selectOption("#assembly-step", "3");
  await page.click("#assembly-close");
  assert.deepEqual(
    await page.evaluate(() =>
      window.__actuator.meshes.map((m) => ({
        color: m.material.color.getHex(),
        opacity: m.material.opacity,
        transparent: m.material.transparent,
        depthWrite: m.material.depthWrite,
      })),
    ),
    original,
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await page.click("#assembly-guide");
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
    true,
  );
  assert.deepEqual(errors, []);
  console.log(
    "Assembly process passed: 20 stages, all BOM references, housing-first order, eight front screws, opaque parts, before/after states, scoped context, blocked playback, restore and mobile layout.",
  );
} finally {
  await browser.close();
}
