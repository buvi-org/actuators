import "./style.css";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { initLaminations } from "./lamination-view.js";

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
const meshes = [],
  materialCopies = new Map();
const clipPlane = new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0);
const setDirty = () => {
  needsRender = true;
};

function defaultDetails() {
  $("component-detail").innerHTML =
    `<div class="detail-icon">◈ <small>REFERENCE ASSEMBLY</small></div><h2 class="detail-title">AK80-9 V3.0</h2><span class="pill">Manufacturer geometry</span><p class="detail-desc">Explore the physical assembly. Select a component in the model or assembly tree to inspect its specifications.</p><dl class="detail-grid"><div><dt>CAD instances</dt><dd>${manifest.mesh_count} / ${new Set(manifest.parts.map((p) => p.bomId)).size} part types</dd></div><div><dt>Measured envelope</dt><dd>Ø${manifest.envelope_mm[0]} × ${manifest.envelope_mm[2]} mm</dd></div><div><dt>Model units</dt><dd>Metres / dimensions shown in mm</dd></div><div><dt>Source</dt><dd>CubeMars V3.0 STEP</dd></div></dl><h3 class="detail-heading">DESIGN MATURITY</h3><p class="open-note">Reference geometry is not a fabrication release. Unmodelled motor and gear internals are tracked in the BOM.</p>`;
}

function selectPart(id) {
  selected = id;
  document
    .querySelectorAll(".part-row")
    .forEach((e) => e.classList.toggle("selected", e.dataset.id === id));
  if (!id) {
    defaultDetails();
    updateScene();
    return;
  }
  const part = bom.find((r) => r.id === id);
  const source = manifest.parts.find((p) => p.bomId === id);
  const fields = Object.entries(part.specifications)
    .map(([k, v]) => `<div><dt>${escape(k)}</dt><dd>${escape(v)}</dd></div>`)
    .join("");
  $("component-detail").innerHTML =
    `<div class="detail-icon" style="color:${source.color}">◈ <small>${id}</small></div><h2 class="detail-title">${escape(part.name)}</h2><span class="pill">${escape(part.status)}</span><dl class="detail-grid"><div><dt>Quantity in assembly</dt><dd>${part.quantity} ${part.unit}</dd></div>${fields}<div><dt>Material</dt><dd>${escape(part.material)}</dd></div><div><dt>Make / buy</dt><dd>${escape(part.process)}</dd></div><div><dt>Source part name</dt><dd>${escape(source.sourceName)}</dd></div></dl><div class="inspector-actions"><button id="isolate-part">${isolated === id ? "Show all" : "Isolate part"}</button><button id="hide-part">${hiddenIds.has(id) ? "Show part" : "Hide part"}</button></div><h3 class="detail-heading">BEFORE MANUFACTURE</h3><p class="open-note">${escape(part.unresolved)}</p>`;
  $("isolate-part").onclick = () => {
    isolated = isolated === id ? null : id;
    hiddenIds.delete(id);
    selectPart(id);
    fitView();
  };
  $("hide-part").onclick = () => {
    hiddenIds.has(id) ? hiddenIds.delete(id) : hiddenIds.add(id);
    selectPart(id);
  };
  updateScene();
}

function renderParts() {
  const query = $("part-search").value.toLowerCase();
  const groups = [...new Set(manifest.parts.map((p) => p.group))];
  $("parts-list").innerHTML =
    groups
      .map((group) => {
        const unique = [
          ...new Map(
            manifest.parts
              .filter((p) => p.group === group)
              .map((p) => [p.bomId, p]),
          ).values(),
        ].filter((p) => (p.name + " " + p.bomId).toLowerCase().includes(query));
        if (!unique.length) return "";
        return (
          `<h3 class="part-group">${group}</h3>` +
          unique
            .map(
              (p) =>
                `<button class="part-row ${selected === p.bomId ? "selected" : ""}" data-id="${p.bomId}"><span class="part-color" style="background:${p.color}"></span><span>${escape(p.name)}</span><small>×${bom.find((r) => r.id === p.bomId).quantity}</small></button>`,
            )
            .join("")
        );
      })
      .join("") || '<p class="empty">No matching components.</p>';
  document
    .querySelectorAll(".part-row")
    .forEach((b) => (b.onclick = () => selectPart(b.dataset.id)));
}

function updateScene() {
  for (const mesh of meshes) {
    const p = mesh.userData.part;
    if (!p) continue;
    mesh.position.z = mesh.userData.baseZ + p.explode * separation;
    mesh.visible =
      !hiddenIds.has(p.bomId) && (!isolated || isolated === p.bomId);
    mesh.material.clippingPlanes = section ? [clipPlane] : [];
    mesh.material.emissive.set(selected === p.bomId ? "#4eaf89" : "#000000");
    mesh.material.emissiveIntensity = selected === p.bomId ? 0.27 : 0;
    mesh.material.needsUpdate = true;
  }
  $("assembled").classList.toggle("active", separation === 0 && !section);
  $("exploded").classList.toggle("active", separation > 0 && !section);
  $("section").classList.toggle("active", section);
  $("explode-range").value = Math.round(separation * 100);
  $("explode-value").textContent = `${Math.round(separation * 100)}%`;
  $("view-caption").textContent = section
    ? "CLIPPED SECTION / SURFACES ARE NOT CAPPED"
    : separation
      ? "EXPLODED REFERENCE / OFFSETS FOR INSPECTION"
      : "CUBEMARS REFERENCE GEOMETRY";
  setDirty();
}

function fitView() {
  if (!model) return;
  model.updateMatrixWorld(true);
  const box = new THREE.Box3();
  meshes.filter((m) => m.visible).forEach((m) => box.expandByObject(m));
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
  model = gltf.scene;
  scene.add(model);
  model.traverse((object) => {
    if (!object.isMesh) return;
    let node = object;
    let part;
    while (node && !part) {
      part = manifest.parts.find((p) => p.id === node.name);
      node = node.parent;
    }
    if (!part) return;
    object.userData.part = part;
    object.userData.baseZ = object.position.z;
    object.material = object.material.clone();
    object.material.color.set(part.color);
    object.material.metalness = 0.42;
    object.material.roughness = 0.4;
    object.material.envMapIntensity = 0.75;
    object.material.side = THREE.DoubleSide;
    materialCopies.set(object.uuid, object.material);
    meshes.push(object);
  });
  if (meshes.length !== manifest.mesh_count)
    throw new Error(
      `Expected ${manifest.mesh_count} parts, loaded ${meshes.length}`,
    );
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
      .find((h) => !section || clipPlane.distanceToPoint(h.point) >= 0);
    if (hit) selectPart(hit.object.userData.part.bomId);
  });
  renderer.setAnimationLoop(() => {
    controls.update();
    if (needsRender && !$("model-panel").hidden) {
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
    fitView,
    selectPart,
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
    fitView();
  };
  $("assembled").onclick = () => {
    separation = 0;
    section = false;
    updateScene();
    fitView();
  };
  $("exploded").onclick = () => {
    separation = 0.65;
    section = false;
    updateScene();
    fitView();
  };
  $("section").onclick = () => {
    section = !section;
    updateScene();
  };
  $("explode-range").oninput = (e) => {
    separation = Number(e.target.value) / 100;
    updateScene();
  };
  $("explode-range").onchange = fitView;
  $("reset-view").onclick = fitView;
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
