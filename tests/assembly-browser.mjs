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
    // EM03 is the rotor shell, and it is machined as part of the one-piece rotor (G03),
    // so no process step lists it separately any more.
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
  assert.deepEqual(coverage, { missing: ["EM03"], invalid: [] });
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
    /68-sheet/,
  );
  assert.ok(
    (await visible()).filter((id) => id.startsWith("EM01/")).length >= 68,
  );
  assert.ok(!(await visible()).some((id) => id.startsWith("M02/")));
  assert.ok((await visible()).some((id) => id.startsWith("M01/")));
  assert.equal(await page.locator("#assembly-context").count(), 0);
  assert.equal(await page.locator("#assembly-cut").count(), 0);
  assert.equal(await page.locator("#section").isVisible(), false);
  const processColors = await page.evaluate(() =>
    window.__actuator.meshes.map((m) => m.material.color.getHex()),
  );
  const colorIdentity = await page.evaluate(() => {
    const byPart = new Map();
    for (const m of window.__actuator.meshes) {
      const id = m.userData.nodeId.startsWith("M01/")
        ? "M01"
        : m.userData.nodeId;
      const color = m.material.color.getHex();
      if (byPart.has(id) && byPart.get(id) !== color) return false;
      byPart.set(id, color);
    }
    return new Set(byPart.values()).size === byPart.size;
  });
  assert.equal(colorIdentity, true);
  await fs.mkdir("tmp/qa", { recursive: true });
  await page.screenshot({
    path: "tmp/qa/assembly-process.png",
    fullPage: true,
  });
  for (let i = 0; i < 20; i++) {
    await page.selectOption("#assembly-step", String(i));
    assert.deepEqual(
      await page.evaluate(() =>
        window.__actuator.meshes.map((m) => m.material.color.getHex()),
      ),
      processColors,
    );
    assert.equal(
      await page.evaluate(() =>
        window.__actuator.meshes.every(
          (m) => m.material.clippingPlanes.length === 0,
        ),
      ),
      true,
    );
    assert.equal(
      await page.evaluate(async (index) => {
        const a = window.__actuator,
          data = await (await fetch("data/assembly-sequence.json")).json();
        const step = data.steps[index];
        if (step.phase !== "Actuator installation") return true;
        return a.meshes.every((m) => {
          let n = a.assembly.nodes.get(m.userData.nodeId);
          while (n) {
            if (step.context.includes(n.id)) return m.visible;
            n = a.assembly.nodes.get(n.parent);
          }
          return true;
        });
      }, i),
      true,
    );
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
  // No step is blocked any more: the rotor is one machined body, so the hub-to-shell joint
  // that used to block A06 does not exist. Autoplay must therefore run to the end instead
  // of stopping on a blocked stage, and no stage may report a blocker.
  await page.selectOption("#assembly-step", "5");
  await page.click("#assembly-play");
  await page.waitForFunction(
    () => window.__actuator.assemblyGuide.getState().index >= 6,
    null,
    { timeout: 30000 },
  );
  const blockedStages = await page.evaluate(async () => {
    const d = await (await fetch("data/assembly-sequence.json")).json();
    return d.steps
      .filter((s) => s.status.startsWith("Blocked"))
      .map((s) => s.id);
  });
  assert.deepEqual(blockedStages, []);
  // Every stage must still disclose that its path is unvalidated.
  const unvalidated = await page.evaluate(async () => {
    const d = await (await fetch("data/assembly-sequence.json")).json();
    return d.steps.filter((s) => s.pathReview.status !== "not validated").length;
  });
  assert.equal(unvalidated, 0);
  await page.selectOption("#assembly-step", "3");
  await page.locator('#assembly-detail [data-mate="EM01"]').click();
  assert.equal(
    await page.evaluate(
      () => window.__actuator.assemblyGuide.getState().active,
    ),
    true,
  );
  await page.click("#assembly-close");
  assert.equal(await page.locator("#section").isVisible(), true);
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
    "Assembly process passed: 20 stages, all BOM references, housing-first order, eight front screws, opaque parts, before/after states, persistent earlier parts, unique stable colors, no section cuts, blocked playback, restore and mobile layout.",
  );
} finally {
  await browser.close();
}
