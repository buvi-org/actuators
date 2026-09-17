import * as THREE from "three";
import { belongsTo } from "./assembly-model.js";

export function initAssemblyGuide({
  data,
  assembly,
  meshes,
  scene,
  camera,
  controls,
  selectPart,
  updateScene,
  setDirty,
}) {
  const $ = (id) => document.getElementById(id);
  const escape = (value) =>
    String(value).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  let active = false,
    index = 0;
  const original = new Map(
    meshes.map((m) => [
      m,
      {
        opacity: m.material.opacity,
        transparent: m.material.transparent,
        depthWrite: m.material.depthWrite,
        color: m.material.color.clone(),
      },
    ]),
  );
  const overlay = new THREE.Group();
  scene.add(overlay);
  const matches = (mesh, ids) =>
    ids.some((id) => belongsTo(assembly.nodes, mesh.userData.nodeId, id));
  const labels = (ids) =>
    ids
      .map(
        (id) =>
          `<button class="mate-part" data-mate="${escape(id)}">${escape(assembly.nodes.get(id)?.name || id)} · ${escape(id)}</button>`,
      )
      .join(" ");
  $("assembly-step").innerHTML = data.steps
    .map((s, i) => `<option value="${i}">${i + 1}. ${escape(s.title)}</option>`)
    .join("");
  $("assembly-register").innerHTML =
    `<summary>${data.steps.length} joint reviews / order unvalidated</summary><p>${escape(data.scope)}</p><div class="joint-table"><table><thead><tr><th>Operation</th><th>Parts / counterparts</th><th>Surfaces</th><th>Method / release check</th></tr></thead><tbody>${data.steps.map((s, i) => `<tr><td><button data-step="${i}">${s.id} · ${escape(s.title)}</button><p>${escape(s.status)}</p></td><td>${escape(s.parts.join(", "))}<br>↔ ${escape(s.target.join(", ") || "Fixture")}</td><td>${s.surfaces.map(escape).join("<br>")}</td><td>${escape(s.method)}<p>${escape(s.check)}</p></td></tr>`).join("")}</tbody></table></div>`;
  $("assembly-register")
    .querySelectorAll("[data-step]")
    .forEach(
      (b) =>
        (b.onclick = () => {
          if (!active) start();
          go(Number(b.dataset.step));
        }),
    );
  function clearOverlay() {
    for (const child of [...overlay.children]) {
      child.geometry.dispose();
      child.material.dispose();
      overlay.remove(child);
    }
  }
  function showDetails() {
    const s = data.steps[index];
    $("assembly-step").value = String(index);
    $("assembly-detail").innerHTML =
      `<small>ASSEMBLY ${s.id} / ${index + 1} OF ${data.steps.length}</small><h3>${escape(s.title)}</h3><p class="assembly-warning">${escape(s.status)}</p><h4>Part under review · amber</h4>${labels(s.parts)}<h4>Mates with · cyan</h4>${labels(s.target)}<h4>Installation path withheld</h4><p class="assembly-warning">${escape(s.pathReview.reason)}</p><h4>Contact / clearance surfaces</h4><ul>${s.surfaces.map((t) => `<li>${escape(t)}</li>`).join("")}</ul><h4>${escape(s.method)}</h4><p>${escape(s.process)}</p><h4>Required before release</h4><p>${escape(s.check)}</p><p class="assembly-note">${s.marker ? "Cyan annulus marks the nominal axial seat listed above; it is an analytic annotation, not a selected CAD face." : "Colored parts identify the joint participants. Exact CAD face highlighting is unavailable for this joint; surfaces are described above."}</p><p class="assembly-note">Static mating review only. All parts stay at their current model positions, which can still contain the documented interferences. Review numbering does not establish an assembly order. Click a part for its full component record below.</p>`;
    $("assembly-detail")
      .querySelectorAll("[data-mate]")
      .forEach(
        (b) =>
          (b.onclick = () => {
            selectPart(b.dataset.mate);
            draw();
          }),
      );
    clearOverlay();
    if (s.marker) {
      const [inner, outer, z] = s.marker;
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(inner / 1000, outer / 1000, 96),
        new THREE.MeshBasicMaterial({
          color: 0x00e8ee,
          transparent: true,
          opacity: 0.75,
          side: THREE.DoubleSide,
          depthTest: false,
          depthWrite: false,
        }),
      );
      ring.position.z = z / 1000;
      ring.renderOrder = 100;
      overlay.add(ring);
    }
  }
  function draw() {
    if (!active) return;
    const s = data.steps[index];
    for (const mesh of meshes) {
      const current = matches(mesh, s.parts),
        target = matches(mesh, s.target);
      mesh.position.copy(mesh.userData.basePosition);
      mesh.visible = true;
      mesh.material.clippingPlanes = [];
      mesh.material.color.copy(
        current
          ? new THREE.Color(0xe5a33e)
          : target
            ? new THREE.Color(0x39bcc8)
            : original.get(mesh).color,
      );
      mesh.material.transparent = true;
      mesh.material.opacity = current ? 1 : target ? 0.65 : 0.1;
      mesh.material.depthWrite = current;
      mesh.material.emissive.set(current ? 0xa76710 : target ? 0x007f88 : 0);
      mesh.material.emissiveIntensity = current || target ? 0.6 : 0;
    }
    $("assembly-prev").disabled = index === 0;
    $("assembly-next").disabled = index === data.steps.length - 1;
    setDirty();
  }
  function go(i) {
    index = THREE.MathUtils.clamp(i, 0, data.steps.length - 1);
    showDetails();
    draw();
  }
  function start() {
    active = true;
    $("assembly-panel").hidden = false;
    $("assembly-detail").hidden = false;
    document.querySelector(".viewport-bottom").hidden = true;
    $("assembly-guide").classList.add("active");
    for (const id of ["assembled", "exploded", "section"])
      $(id).classList.remove("active");
    $("view-caption").textContent = "STATIC JOINT REVIEW / NO VALIDATED PATHS";
    controls.target.set(0, 0, 0);
    camera.position.set(0.15, 0.11, 0.18);
    controls.update();
    go(0);
  }
  function close() {
    if (!active) return;
    active = false;
    clearOverlay();
    for (const mesh of meshes) {
      const { color, ...properties } = original.get(mesh);
      Object.assign(mesh.material, properties);
      mesh.material.color.copy(color);
    }
    $("assembly-panel").hidden = true;
    $("assembly-detail").hidden = true;
    document.querySelector(".viewport-bottom").hidden = false;
    $("assembly-guide").classList.remove("active");
    updateScene();
  }
  $("assembly-guide").onclick = () => (active ? close() : start());
  $("assembly-close").onclick = close;
  $("assembly-prev").onclick = () => go(index - 1);
  $("assembly-next").onclick = () => go(index + 1);
  $("assembly-step").onchange = (e) => go(Number(e.target.value));
  // Other view/visibility modes restore the normal material and visibility state first.
  for (const id of [
    "assembled",
    "exploded",
    "section",
    "internal-view",
    "mounting-view",
    "gear-view",
    "show-all",
    "all-parts",
    "parts-list",
  ])
    $(id).addEventListener("click", close, { capture: true });
  return {
    close,
    refresh: draw,
    getState: () => ({ active, playing: false, index, progress: 0 }),
  };
}
