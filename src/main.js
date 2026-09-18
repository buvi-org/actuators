import "./style.css";
import { initAssemblyGuide } from "./assembly-guide.js";
import { sectionDiagram } from "./part-diagram.js";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { GLTFExporter } from "three/addons/exporters/GLTFExporter.js";
import { initLaminations } from "./lamination-view.js";
import { buildAssembly, belongsTo, inheritedHidden } from "./assembly-model.js";

const $ = (id) => document.getElementById(id);
const escape = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const base = import.meta.env.BASE_URL;
async function getJSON(path) {
  const response = await fetch(base + path);
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  return response.json();
}

let manifest,
  bom,
  specs,
  driverInventory,
  model,
  renderer,
  camera,
  controls,
  scene;
let selected = null,
  isolated = null,
  hiddenIds = new Set(),
  separation = 0,
  section = false,
  needsRender = true;
let assembly;
let assemblyGuide;
const expanded = new Set([
  "root",
  "group:stator",
  "group:rotor",
  "group:transmission",
  "group:bearings",
  "group:structure",
  "group:electronics",
]);
const meshes = [];
const clipPlane = new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0);
const setDirty = () => {
  needsRender = true;
};

function defaultDetails() {
  $("component-detail").innerHTML =
    `<h2 class="detail-title">Complete assembly study</h2><span class="pill amber">Reference CAD + provisional internals</span><p class="detail-desc">Every BOM component is in the tree. Expand components to inspect individual laminations, coatings, coils, magnets and fasteners. Checkboxes control visibility of a component and its children.</p><dl class="detail-grid"><div><dt>Manufacturer reference</dt><dd>43 source CAD instances; sun blank replaced in study</dd></div><div><dt>Added motor study</dt><dd>68 steel laminations · 136 coatings · 36 winding bundles · 42 illustrative magnet segments</dd></div></dl><p class="open-note">Added internals are an illustrative layout, not a recovered OEM design or a validated fit. Select any item to see the evidence and assumptions.</p>`;
}
function affectedMeshes(id) {
  return assembly
    ? meshes.filter((m) => belongsTo(assembly.nodes, m.userData.nodeId, id))
    : [];
}
function toggleVisibility(id) {
  const items = affectedMeshes(id),
    visible = items.some((m) => m.visible);
  if (visible) hiddenIds.add(id);
  else {
    if (isolated && !belongsTo(assembly.nodes, id, isolated)) isolated = null;
    for (const key of [...hiddenIds])
      if (
        belongsTo(assembly.nodes, id, key) ||
        belongsTo(assembly.nodes, key, id)
      )
        hiddenIds.delete(key);
  }
  updateScene();
  renderParts();
  if (selected) selectPart(selected, false);
}
function selectPart(id, refreshTree = true) {
  if (id?.startsWith("G02/")) id = "G02";
  if (!assembly) {
    defaultDetails();
    return;
  }
  const node = assembly.nodes.get(id);
  if (!node) {
    selected = null;
    defaultDetails();
    updateScene();
    return;
  }
  selected = id;
  let parent = node,
    row = node.row;
  while (parent && !row) {
    parent = assembly.nodes.get(parent.parent);
    row = parent?.row;
  }
  let ancestor = node;
  while (ancestor) {
    expanded.add(ancestor.parent);
    ancestor = assembly.nodes.get(ancestor.parent);
  }
  if (refreshTree) renderParts();
  const entry = (k, v) =>
    `<div><dt>${escape(k)}</dt><dd>${escape(v)}</dd></div>`;
  let detail = "";
  if (node.electronic) {
    const e = node.electronic;
    detail +=
      entry("Reference designator", e.reference) +
      entry("Category", e.category) +
      entry("Source CAD occurrences", e.quantity) +
      entry("Package model labels", e.packageModels.join(", ")) +
      entry(
        "Value / rating / tolerance / exact MPN",
        "Unknown — package labels are not device identification",
      ) +
      entry("Evidence", e.evidence);
  }
  if (row) {
    detail +=
      entry("BOM identifier", row.id) +
      entry("Engineering quantity", `${row.quantity ?? "TBD"} ${row.unit}`) +
      entry("Evidence status", row.status) +
      Object.entries(row.specifications)
        .map(([k, v]) => entry(k, v))
        .join("") +
      entry("Material", row.material) +
      entry("Make / buy", row.process) +
      entry("Parent", row.parent || node.parent) +
      entry(
        "Cost",
        row.unitCost === null
          ? "Not quoted"
          : `${row.unitCost} ${row.currency}`,
      ) +
      entry(
        "Procurement release",
        row.procurementReady ? "Released" : "Not released",
      );
  }
  if (node.part) {
    detail +=
      entry("Source part name", node.part.sourceName) +
      entry("CAD occurrence", node.part.id) +
      entry("CAD dimensions (mm)", node.part.dimensions_mm.join(" × ")) +
      entry("CAD bounding coordinates (mm)", node.part.bounds_mm.join(", ")) +
      entry("CAD solid volume (mm³)", node.part.volume_mm3) +
      entry("Source solid count", node.part.solids);
  }
  if (node.description)
    detail += entry("Geometry / interpretation", node.description);
  const items = affectedMeshes(id),
    reference = items.filter(
      (m) => m.userData.geometryKind === "reference",
    ).length,
    study = items.length - reference;
  detail +=
    entry(
      "3D representation",
      items.length
        ? `${reference} reference meshes; ${study} provisional meshes`
        : "Data record — no individually located 3D body",
    ) +
    entry(
      "Currently visible",
      `${items.filter((m) => m.visible).length} of ${items.length} bodies`,
    );
  if (node.kind === "assembly")
    detail += entry("Direct child records", node.children.length);
  const sourceIds = row?.sources || [];
  const sources = sourceIds
    .map((key) => {
      const source = specs.sources.find((s) => s.id === key);
      return source
        ? `<a href="${source.url}" target="_blank" rel="noreferrer">${key} / ${escape(source.name)} ↗</a>`
        : "";
    })
    .join("");
  $("component-detail").innerHTML =
    `<h2 class="detail-title">${escape(node.name)}</h2><span class="pill ${study || !items.length ? "amber" : ""}">${escape(node.status || "Assembly group")}</span>${["EM03", "EM04"].includes(row?.id) ? `<p class="open-note">Primeform proposal: nothing in the source CAD joins the measured hub (O44.5 flange face) to the magnets, so this end bell is an invention whose form follows the hub's own six-spoke pattern. Its joint to the hub is undefined: no fit, key, screw or bond. The magnets' radial band also does not match the arcuate slots in the source housings, so rotor radial placement is unproven.</p>` : ""}${row?.id === "M02" ? `<p class="open-note">No axial clash: the rotor end bell moved 4.5 mm forward of its earlier position, which removed the previous 194.333 mm3 overlap with this housing.</p>` : ""}${row?.id === "M01" ? `<p class="open-note">Primeform R4: the stator seat stays at its Choice C position (z 11.436 mm) so the ring remains clamped by the eight front screws. Gold bodies are added support and seat material; hide them to compare the original housing.</p><a href="${base}design/main-housing-supported.step" download>Modified housing STEP ↓</a>` : ""}${["G02", "G04", "G05"].includes(row?.id) ? `<p><a href="${base}design/provisional-${{ G02: "sun", G04: "planet", G05: "ring" }[row.id]}-gear.step" download>Single-solid gear STEP ↓</a><br><a href="${base}design/provisional-gear-train.step" download>Gear assembly STEP ↓</a></p>` : ""}<div class="inspector-actions"><button id="isolate-part" ${items.length ? "" : "disabled"}>${isolated === id ? "Exit isolate" : "Isolate"}</button><button id="hide-part" ${items.length ? "" : "disabled"}>${items.some((m) => m.visible) ? "Hide" : "Show"}</button><button id="focus-part" ${items.length ? "" : "disabled"}>Focus</button></div>${items.length ? sectionDiagram(items, `${escape(node.name)} — axial section, dimensions in mm`) : ""}<dl class="detail-grid">${detail}</dl>${row?.unresolved ? `<h3 class="detail-heading">UNRESOLVED DETAILS</h3><p class="open-note">${escape(row.unresolved)}</p>` : ""}<div class="detail-sources">${sources}${node.electronic ? `<a href="${node.electronic.source}" target="_blank" rel="noreferrer">Driver STEP source ↗</a>` : ""}</div>`;
  $("isolate-part").onclick = () => {
    isolated = isolated === id ? null : id;
    for (const key of [...hiddenIds])
      if (
        belongsTo(assembly.nodes, id, key) ||
        belongsTo(assembly.nodes, key, id)
      )
        hiddenIds.delete(key);
    updateScene();
    renderParts();
    selectPart(id, false);
    fitView();
  };
  $("hide-part").onclick = () => toggleVisibility(id);
  $("focus-part").onclick = () => fitView(id);
  updateScene();
}
function renderParts() {
  if (!assembly) return;
  const query = $("part-search").value.toLowerCase(),
    holder = $("parts-list"),
    scroll = holder.scrollTop;
  const matches = (id) => {
    const n = assembly.nodes.get(id);
    return (
      `${n.id} ${n.name} ${n.row ? JSON.stringify(n.row) : ""}`
        .toLowerCase()
        .includes(query) || n.children.some(matches)
    );
  };
  const line = (id, depth) => {
    const n = assembly.nodes.get(id);
    const treeChildren = id === "G02" ? [] : n.children;
    if (query && !matches(id)) return "";
    const items = affectedMeshes(id),
      visible = items.filter((m) => m.visible).length,
      open = expanded.has(id) || !!query;
    const type =
      n.kind === "component"
        ? n.row.id
        : n.kind === "electronic"
          ? "PCB"
          : n.status === "Reference CAD"
            ? "CAD"
            : n.kind === "assembly"
              ? ""
              : "STUDY";
    return `<div class="tree-node" style="--depth:${depth}"><button class="tree-expand" data-expand="${id}" aria-label="${open ? "Collapse" : "Expand"} ${escape(n.name)}" ${treeChildren.length ? "" : "disabled"}>${treeChildren.length ? (open ? "▾" : "▸") : "·"}</button><input type="checkbox" data-visible="${id}" aria-label="Visibility: ${escape(n.name)}" ${visible ? "checked" : ""} ${items.length ? "" : "disabled"} title="${items.length ? "Show/hide this item and its children" : "No individually located geometry in available sources"}"><button class="part-row ${selected === id ? "selected" : ""}" data-id="${id}" title="${escape(n.name)}"><span>${escape(n.name)}</span><small>${type}</small></button></div>${open ? treeChildren.map((child) => line(child, depth + 1)).join("") : ""}`;
  };
  holder.innerHTML =
    assembly.nodes
      .get("root")
      .children.map((id) => line(id, 0))
      .join("") || '<p class="empty">No matching components.</p>';
  holder
    .querySelectorAll("[data-id]")
    .forEach((b) => (b.onclick = () => selectPart(b.dataset.id)));
  holder.querySelectorAll("[data-expand]").forEach(
    (b) =>
      (b.onclick = () => {
        expanded.has(b.dataset.expand)
          ? expanded.delete(b.dataset.expand)
          : expanded.add(b.dataset.expand);
        renderParts();
      }),
  );
  holder.querySelectorAll("[data-visible]").forEach((e) => {
    const items = affectedMeshes(e.dataset.visible),
      v = items.filter((m) => m.visible).length;
    e.indeterminate = v > 0 && v < items.length;
    e.onchange = () => toggleVisibility(e.dataset.visible);
  });
  holder.scrollTop = scroll;
}
function updateScene() {
  if (!assembly) return;
  for (const mesh of meshes) {
    const id = mesh.userData.nodeId;
    mesh.position.copy(mesh.userData.basePosition);
    mesh.position.z += mesh.userData.explode * separation;
    mesh.visible =
      !inheritedHidden(assembly.nodes, id, hiddenIds) &&
      (!isolated || belongsTo(assembly.nodes, id, isolated));
    mesh.material.clippingPlanes = section ? [clipPlane] : [];
    const highlight = selected && belongsTo(assembly.nodes, id, selected);
    mesh.material.emissive.set(highlight ? "#4eaf89" : "#000000");
    mesh.material.emissiveIntensity = highlight ? 0.16 : 0;
    mesh.material.needsUpdate = true;
  }
  $("assembled").classList.toggle("active", separation === 0 && !section);
  $("exploded").classList.toggle("active", separation > 0 && !section);
  $("section").classList.toggle("active", section);
  $("explode-range").value = Math.round(separation * 100);
  $("explode-value").textContent = `${Math.round(separation * 100)}%`;
  $("view-caption").textContent = section
    ? "CLIPPED SECTION / UNCAPPED"
    : "REFERENCE CAD + PROVISIONAL INTERNALS";
  assemblyGuide?.refresh();
  setDirty();
}

function fitView(id = null) {
  if (!model) return;
  model.updateMatrixWorld(true);
  const box = new THREE.Box3();
  meshes
    .filter(
      (m) =>
        m.visible && (!id || belongsTo(assembly.nodes, m.userData.nodeId, id)),
    )
    .forEach((m) => box.expandByObject(m));
  if (box.isEmpty()) return;
  const center = box.getCenter(new THREE.Vector3()),
    size = box.getSize(new THREE.Vector3());
  const fov = THREE.MathUtils.degToRad(camera.fov);
  const radius = size.length() / 2;
  const distance =
    (radius /
      Math.sin(
        Math.min(fov, 2 * Math.atan(Math.tan(fov / 2) * camera.aspect)) / 2,
      )) *
    1.18;
  camera.position
    .copy(center)
    .add(
      new THREE.Vector3(0.88, 0.66, 1.3).normalize().multiplyScalar(distance),
    );
  controls.target.copy(center);
  controls.update();
  setDirty();
}

function renderBOM() {
  const query = $("bom-search").value.toLowerCase(),
    filter = $("bom-filter").value;
  const data = bom.filter(
    (r) =>
      JSON.stringify(r).toLowerCase().includes(query) &&
      (filter === "all" ||
        (filter === "cad" ? r.instances.length > 0 : r.instances.length === 0)),
  );
  $("bom-results").textContent = `${data.length} of ${bom.length} items`;
  $("bom-body").innerHTML = data.length
    ? data
        .map(
          (r) =>
            `<tr><td><span class="id">${r.id}${r.parent ? " / included in " + r.parent : ""}</span><strong>${escape(r.name)}</strong><small>${escape(r.group)}</small></td><td>${r.quantity ?? "TBD"}<small>${r.unit}</small></td><td>${Object.entries(
              r.specifications,
            )
              .map(
                ([k, v]) =>
                  `<div><strong style="font-size:10px">${escape(k)}</strong><br>${escape(v)}</div>`,
              )
              .join(
                "<br>",
              )}</td><td>${escape(r.material)}<small>${escape(r.process)}</small></td><td><span class="pill ${r.instances.length ? "" : "amber"}">${escape(r.status)}</span><br>${escape(r.unresolved)}<small>${
              r.sources
                .map((id) => {
                  const s = specs.sources.find((s) => s.id === id);
                  return `<a target="_blank" rel="noreferrer" href="${s.url}">${id} ↗</a>`;
                })
                .join(" · ") || "Engineering requirement"
            }</small></td></tr>`,
        )
        .join("")
    : '<tr><td colspan="5">No matching components.</td></tr>';
}

function renderSpecs() {
  const card = (title, dict) =>
    `<article class="spec-card"><h3>${title}</h3><dl>${Object.entries(dict)
      .map(([k, v]) => `<div><dt>${escape(k)}</dt><dd>${escape(v)}</dd></div>`)
      .join("")}</dl></article>`;
  $("spec-content").innerHTML =
    `<div class="spec-grid"><div>${card("Published actuator data", specs.published)}<br>${card("Compatible driver · current manual", specs.driver)}</div><div>${card("Mechanical interfaces", specs.interfaces)}<br>${card("Calculated from published values", specs.derived)}<br><article class="spec-card"><h3>Interpretation limits</h3><ul>${specs.cautions.map((c) => `<li>${escape(c)}</li>`).join("")}</ul></article></div></div><div class="sources"><h3>Source register · checked ${specs.sourceDate}</h3>${specs.sources.map((s) => `<a href="${s.url}" target="_blank" rel="noreferrer">${s.id} / ${escape(s.name)} ↗</a>`).join("")}</div>`;
}

function renderDriver() {
  const q = $("driver-search").value.toLowerCase();
  const rows = driverInventory.components.filter((r) =>
    [r.reference, r.category, ...r.packageModels]
      .join(" ")
      .toLowerCase()
      .includes(q),
  );
  $("driver-results").textContent =
    `${rows.length} of ${driverInventory.referenceDesignators} designators`;
  $("driver-body").innerHTML =
    rows
      .map(
        (r) =>
          `<tr><td><strong>${r.reference}</strong></td><td>${escape(r.category)}</td><td>${r.quantity}</td><td>${r.packageModels.map(escape).join("<br>") || "Unresolved"}</td><td>Unknown</td></tr>`,
      )
      .join("") || '<tr><td colspan="5">No matching designators.</td></tr>';
}

async function init3D() {
  const view = $("viewport");
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0, 0);
  renderer.localClippingEnabled = true;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1;
  view.appendChild(renderer.domElement);
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(36, 1, 0.0005, 10);
  camera.position.set(0.15, 0.11, 0.22);
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.minDistance = 0.035;
  controls.maxDistance = 1.5;
  controls.addEventListener("change", setDirty);
  const environment = new RoomEnvironment();
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envTarget = pmrem.fromScene(environment, 0.04);
  scene.environment = envTarget.texture;
  environment.dispose();
  pmrem.dispose();
  scene.add(new THREE.HemisphereLight(0xffffff, 0x66777a, 1.4));
  const light = new THREE.DirectionalLight(0xffffff, 2);
  light.position.set(0.15, 0.2, 0.3);
  scene.add(light);
  const grid = new THREE.GridHelper(0.35, 35, 0x73898f, 0x9aafb3);
  grid.position.y = -0.057;
  grid.material.transparent = true;
  grid.material.opacity = 0.22;
  scene.add(grid);
  const resize = () => {
    const w = view.clientWidth,
      h = view.clientHeight;
    if (!w || !h) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    setDirty();
  };
  new ResizeObserver(resize).observe(view);
  resize();
  const gltf = await new GLTFLoader().loadAsync(
    base + "models/ak80-9-reference.glb",
  );
  const housingSupports = await new GLTFLoader().loadAsync(
    base + "design/housing-boss-extensions.glb",
  );
  const sunSolid = await new GLTFLoader().loadAsync(
    base + "design/provisional-sun-gear.glb",
  );
  const [planetSolid, ringSolid, rotorSolid, rotorParams, rotorHubSolid] =
    await Promise.all([
    new GLTFLoader().loadAsync(base + "design/provisional-planet-gear.glb"),
    new GLTFLoader().loadAsync(base + "design/provisional-ring-gear.glb"),
    new GLTFLoader().loadAsync(base + "design/rotor-flange.glb"),
    getJSON("design/viewer-rotor-params.json"),
    new GLTFLoader().loadAsync(base + "design/oem-rotor-hub.glb"),
  ]);
  assembly = buildAssembly(
    bom,
    manifest,
    driverInventory,
    gltf.scene,
    housingSupports.scene,
    sunSolid.scene,
    planetSolid.scene,
    ringSolid.scene,
    rotorSolid.scene,
    rotorParams,
    rotorHubSolid.scene,
  );
  model = assembly.root;
  scene.add(model);
  meshes.push(...assembly.meshes);
  hiddenIds = new Set([
    "M01",
    "M02",
    "M03",
    "EM05",
    "EM06",
    "C01",
    "C03",
    "C04",
  ]);
  $("part-count").textContent = `${bom.length} BOM items`;
  updateScene();
  renderParts();
  defaultDetails();
  updateScene();
  fitView();
  $("loading").hidden = true;
  const raycaster = new THREE.Raycaster(),
    pointer = new THREE.Vector2();
  let down;
  renderer.domElement.addEventListener("pointerdown", (e) => {
    down = [e.clientX, e.clientY];
  });
  renderer.domElement.addEventListener("pointerup", (e) => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5)
      return;
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.set(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      (-(e.clientY - rect.top) / rect.height) * 2 + 1,
    );
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster
      .intersectObjects(
        meshes.filter((m) => m.visible),
        false,
      )
      .find((h) =>
        (h.object.material.clippingPlanes || []).every(
          (plane) => plane.distanceToPoint(h.point) >= 0,
        ),
      );
    if (hit) selectPart(hit.object.userData.nodeId);
  });
  const assemblySequence = await getJSON("data/assembly-sequence.json");
  assemblyGuide = initAssemblyGuide({
    data: assemblySequence,
    assembly,
    meshes,
    scene,
    camera,
    controls,
    selectPart,
    updateScene,
    setDirty,
  });
  let processLastFrame = performance.now();
  renderer.setAnimationLoop((now) => {
    assemblyGuide.tick(now - processLastFrame);
    processLastFrame = now;
    controls.update();
    if (needsRender && !$("model-panel").hidden) {
      const distance = camera.position.distanceTo(controls.target);
      camera.near = Math.max(0.00001, distance / 100);
      camera.far = Math.max(1, distance * 10);
      camera.updateProjectionMatrix();
      renderer.render(scene, camera);
      needsRender = false;
    }
  });
  window.__actuator = {
    scene,
    camera,
    renderer,
    model,
    meshes,
    manifest,
    bom,
    assembly,
    assemblySequence,
    toggleVisibility,
    fitView,
    selectPart,
    assemblyGuide,
    getState: () => ({
      selected,
      isolated,
      separation,
      section,
      hiddenIds: [...hiddenIds],
    }),
  };
}

async function init() {
  [manifest, bom, specs, driverInventory] = await Promise.all([
    getJSON("models/manifest.json"),
    getJSON("data/bom.json"),
    getJSON("data/specifications.json"),
    getJSON("data/driver-inventory.json"),
  ]);
  $("part-count").textContent = `${manifest.mesh_count} instances`;
  $("bom-count").textContent = bom.length;
  renderParts();
  renderBOM();
  renderSpecs();
  renderDriver();
  defaultDetails();
  $("driver-search").oninput = renderDriver;
  $("part-search").oninput = renderParts;
  $("bom-search").oninput = renderBOM;
  $("bom-filter").onchange = renderBOM;
  $("all-parts").onclick = () => {
    isolated = null;
    hiddenIds.clear();
    selectPart(null);
    renderParts();
    fitView();
  };
  $("assembled").onclick = () => {
    separation = 0;
    section = false;
    updateScene();
    renderParts();
    fitView();
  };
  $("exploded").onclick = () => {
    separation = 0.65;
    section = false;
    updateScene();
    renderParts();
    fitView();
  };
  $("section").onclick = () => {
    section = !section;
    updateScene();
    renderParts();
  };
  $("explode-range").oninput = (e) => {
    separation = Number(e.target.value) / 100;
    updateScene();
  };
  $("explode-range").onchange = fitView;
  $("reset-view").onclick = () => fitView();
  $("internal-view").onclick = () => {
    isolated = null;
    hiddenIds = new Set([
      "M01",
      "M02",
      "M03",
      "EM05",
      "EM06",
      "C01",
      "C03",
      "C04",
    ]);
    updateScene();
    renderParts();
    fitView();
  };
  $("show-all").onclick = () => {
    $("all-parts").click();
  };
  $("export-assembly").onclick = async () => {
    const button = $("export-assembly");
    button.disabled = true;
    button.textContent = "Exporting…";
    try {
      const clone = model.clone(true);
      clone.userData = {
        kind: "mixed-reference-and-provisional-study",
        note: "Reference CAD with illustrative internals. Not manufacture-ready. Geometry assumptions are recorded by the component tree.",
        bom,
      };
      clone.traverse((o) => {
        if (!o.isMesh) return;
        o.visible = true;
        o.position.copy(o.userData.basePosition);
        o.material = o.material.clone();
        o.material.emissive.set(0);
        o.material.clippingPlanes = [];
        o.userData = {
          id: o.userData.nodeId,
          geometryKind: o.userData.geometryKind,
          details:
            assembly.nodes.get(o.userData.nodeId)?.description ||
            "Manufacturer reference CAD",
        };
      });
      const bytes = await new GLTFExporter().parseAsync(clone, {
        binary: true,
      });
      const url = URL.createObjectURL(
        new Blob([bytes], { type: "model/gltf-binary" }),
      );
      const a = document.createElement("a");
      a.href = url;
      a.download = "ak80-9-complete-study.glb";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
    } finally {
      button.disabled = false;
      button.textContent = "Full assembly GLB ↓";
    }
  };
  $("mounting-view").onclick = () => {
    isolated = null;
    const keep = new Set(["M01", "G05", "EM01", "C03", "F01"]);
    hiddenIds = new Set(
      bom.filter((row) => !keep.has(row.id)).map((row) => row.id),
    );
    const mountScrews = new Set([
      "NAUO7",
      ...Array.from({ length: 7 }, (_, i) => "NAUO" + (22 + i)),
    ]);
    manifest.parts
      .filter((p) => p.bomId === "F01" && !mountScrews.has(p.id))
      .forEach((p) => hiddenIds.add("F01/" + p.id));
    separation = 0;
    section = true;
    updateScene();
    renderParts();
    selectPart("G05");
    fitView();
    const distance = camera.position.distanceTo(controls.target);
    camera.position
      .copy(controls.target)
      .add(
        new THREE.Vector3(1.3, 0.35, -0.8).normalize().multiplyScalar(distance),
      );
    controls.update();
    setDirty();
  };
  $("gear-view").onclick = () => {
    isolated = null;
    hiddenIds = new Set([
      "group:stator",
      "group:rotor",
      "group:structure",
      "group:fasteners",
      "group:electronics",
      "group:consumables",
      "group:bearings",
      "G01",
      "M04",
    ]);
    separation = 0;
    section = false;
    updateScene();
    renderParts();
    selectPart("G02");
    fitView();
  };
  let laminationStarted = false;
  document.querySelectorAll("[data-tab]").forEach(
    (b) =>
      (b.onclick = () => {
        document.querySelectorAll("[data-tab]").forEach((x) => {
          x.classList.toggle("active", x === b);
          x.setAttribute("aria-selected", String(x === b));
        });
        document
          .querySelectorAll(".tab-panel")
          .forEach((p) => (p.hidden = p.id !== b.dataset.tab + "-panel"));
        history.replaceState(null, "", "#" + b.dataset.tab);
        if (b.dataset.tab === "lamination" && !laminationStarted) {
          try {
            initLaminations();
            laminationStarted = true;
          } catch (e) {
            $("lam-error").textContent =
              `Lamination viewer could not load: ${e.message}`;
            $("lam-error").hidden = false;
          }
        }
        setDirty();
      }),
  );
  $("open-lamination").onclick = () =>
    document.querySelector('[data-tab="lamination"]').click();
  const initialTab = [...document.querySelectorAll("[data-tab]")].find(
    (b) => b.dataset.tab === location.hash.slice(1),
  );
  initialTab?.click();
  try {
    await init3D();
  } catch (error) {
    console.error(error);
    $("loading").hidden = false;
    $("loading").innerHTML =
      `<div style="padding:25px;max-width:390px;text-align:center">3D view could not load.<br><br>${escape(error.message)}<br><br>The BOM and specifications remain available. Use a browser with WebGL 2 enabled.</div>`;
  }
}
init().catch((e) => {
  $("loading").textContent = `Project data could not load: ${e.message}`;
  console.error(e);
});
