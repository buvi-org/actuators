import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFExporter } from "three/addons/exporters/GLTFExporter.js";
import {
  defaults,
  calculateStack,
  profilePoints,
  studyPayload,
  profileDXF,
} from "./lamination-math.js";

const $ = (id) => document.getElementById(id);
const fmt = (v, n = 3) => v.toFixed(n);
const download = (value, name, type) => {
  const url = URL.createObjectURL(new Blob([value], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
};

export function initLaminations() {
  let parameters = { ...defaults },
    result,
    spread = 0,
    coatingVisible = true,
    selected = 1,
    viewMode = "stack",
    dirty = true;
  const viewport = $("lam-viewport"),
    scene = new THREE.Scene();
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setClearColor(0, 0);
  viewport.appendChild(renderer.domElement);
  const camera = new THREE.PerspectiveCamera(35, 1, 10, 2000);
  camera.up.set(0, 0, 1);
  camera.position.set(115, -150, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.addEventListener("change", () => (dirty = true));
  scene.add(new THREE.HemisphereLight(0xffffff, 0x546776, 2.5));
  const light = new THREE.DirectionalLight(0xffffff, 2.4);
  light.position.set(80, -80, 180);
  scene.add(light);
  const fill = new THREE.DirectionalLight(0xc7e7ff, 1.3);
  fill.position.set(-100, 80, 50);
  scene.add(fill);
  const stack = new THREE.Group();
  stack.name = "Provisional_lamination_stack_mm";
  scene.add(stack);
  let steel, lowerCoat, upperCoat, geometry;
  const steelMat = new THREE.MeshStandardMaterial({
    color: "#7d8e9b",
    metalness: 0.35,
    roughness: 0.48,
  });
  const coatMat = new THREE.MeshStandardMaterial({
    color: "#68b9a4",
    metalness: 0.05,
    roughness: 0.65,
  });
  const selectedColor = new THREE.Color("#d9a04e"),
    neutral = new THREE.Color("#ffffff");
  function paramsFromInputs() {
    const p = { ...parameters };
    for (const key of Object.keys(defaults)) {
      const el = $("lam-" + key);
      if (el) p[key] = key === "mode" ? el.value : Number(el.value);
    }
    return p;
  }
  function makeGeometry(p) {
    const points = profilePoints(p),
      shape = new THREE.Shape(points.map((v) => new THREE.Vector2(...v)));
    const hole = new THREE.Path();
    hole.absarc(0, 0, p.bore / 2, 0, 2 * Math.PI, true);
    shape.holes.push(hole);
    return new THREE.ExtrudeGeometry(shape, {
      depth: 1,
      bevelEnabled: false,
      curveSegments: 96,
      steps: 1,
    });
  }
  function positionLayers() {
    if (!steel) return;
    const n = result.count,
      c = parameters.coating / 1000,
      t = parameters.steel,
      g = parameters.gap / 1000;
    const visualGap = spread * 1.4;
    const center = result.gross / 2 + (Math.max(0, n - 1) * visualGap) / 2;
    const matrix = new THREE.Matrix4();
    for (let i = 0; i < n; i++) {
      const z = i * (t + 2 * c + g + visualGap) - center;
      for (const [mesh, start, depth] of [
        [steel, z + c, t],
        [lowerCoat, z, c],
        [upperCoat, z + c + t, c],
      ]) {
        matrix.makeScale(1, 1, depth);
        matrix.setPosition(0, 0, start);
        // Single-sheet view hides other instances via zero scale; counts/data remain unchanged.
        if (viewMode === "single" && i !== selected - 1)
          matrix.makeScale(0, 0, 0);
        if (viewMode === "single" && i === selected - 1)
          matrix.setPosition(0, 0, start - z - (t + 2 * c) / 2);
        mesh.setMatrixAt(i, matrix);
      }
      steel.setColorAt(i, i === selected - 1 ? selectedColor : neutral);
    }
    for (const mesh of [steel, lowerCoat, upperCoat]) {
      mesh.instanceMatrix.needsUpdate = true;
      mesh.computeBoundingSphere();
    }
    steel.instanceColor.needsUpdate = true;
    lowerCoat.visible = upperCoat.visible = coatingVisible && c > 0;
    $("lam-spread-label").textContent = spread
      ? `${fmt(visualGap, 2)} mm / sheet (display only)`
      : "True assembled spacing";
    $("lam-layer-readout").textContent =
      `Layer ${selected} of ${n} · steel ${fmt(t, 3)} mm · each coating face ${parameters.coating} µm`;
    dirty = true;
  }
  function fit() {
    const height =
      viewMode === "single"
        ? parameters.steel + (2 * parameters.coating) / 1000
        : result.gross + Math.max(0, result.count - 1) * spread * 1.4;
    const radius = Math.hypot(parameters.od, parameters.od, height) / 2;
    const fov = THREE.MathUtils.degToRad(camera.fov);
    const distance =
      (radius /
        Math.sin(
          Math.min(fov, 2 * Math.atan(Math.tan(fov / 2) * camera.aspect)) / 2,
        )) *
      1.08;
    camera.position.copy(
      new THREE.Vector3(1, -1.35, 0.95).normalize().multiplyScalar(distance),
    );
    controls.target.set(0, 0, 0);
    controls.update();
    dirty = true;
  }
  function renderResults() {
    $("lam-results").innerHTML = [
      ["Sheets", `${result.count}`],
      ["Coated stack", `${fmt(result.gross)} mm`],
      ["Net steel length", `${fmt(result.iron)} mm`],
      ["Axial steel fraction", `${fmt(result.fillFactor * 100, 2)}%`],
      ["Budget remaining", `${fmt(result.remaining)} mm`],
      ["Worst-case safe count", `${result.conservativeCount}`],
    ]
      .map(([k, v]) => `<div><small>${k}</small><strong>${v}</strong></div>`)
      .join("");
    $("lam-tolerance").textContent =
      `For ${result.count} sheets: ${fmt(result.worstMin)}–${fmt(result.worstMax)} mm stack under the entered thickness tolerances. ${result.worstFits ? "The worst-case maximum fits the budget." : "The worst-case maximum exceeds the budget; use the safe count or revise tolerances."}`;
    $("lam-tolerance").classList.toggle("exceeds", !result.worstFits);
    $("lam-equation").textContent =
      `H = N(t + 2c) + (N − 1)g = ${result.count} × (${fmt(parameters.steel)} + 2 × ${fmt(parameters.coating / 1000, 4)}) + ${Math.max(0, result.count - 1)} × ${fmt(parameters.gap / 1000, 4)} = ${fmt(result.gross)} mm`;
    $("lam-layer").max = result.count;
    $("lam-layer").value = selected;
    const coatingSet = [
      ...new Set([0, 1, 2, 3, 5, 10, parameters.coating]),
    ].sort((a, b) => a - b);
    $("lam-comparison").innerHTML = coatingSet
      .map((c) => {
        const r = calculateStack({ ...parameters, coating: c, mode: "budget" });
        return `<tr class="${c === parameters.coating ? "current" : ""}"><td>${c} µm</td><td>${fmt(parameters.steel + (2 * c) / 1000, 3)}</td><td>${r.count}</td><td>${fmt(r.gross)}</td><td>${fmt(r.iron)}</td><td>${fmt(r.fillFactor * 100, 2)}%</td></tr>`;
      })
      .join("");
    $("lam-study-bom").innerHTML =
      `<tr><td>L01</td><td>Provisional steel lamination</td><td>${result.count} ea</td><td>${parameters.steel} mm steel; ${parameters.slots} slots; Ø${parameters.od} / bore Ø${parameters.bore} mm</td></tr><tr><td>L02</td><td>Insulation coating, two faces per sheet</td><td>${2 * result.count} faces</td><td>${parameters.coating} µm / face; ${fmt(result.coatingTotal)} mm total axial contribution</td></tr><tr><td>L03</td><td>Additional inter-sheet gap / adhesive</td><td>${Math.max(0, result.count - 1)} interfaces</td><td>${parameters.gap} µm / interface; ${fmt(result.gapTotal)} mm total axial contribution</td></tr>`;
    $("lam-count-wrap").hidden = parameters.mode !== "count";
  }
  function rebuild() {
    try {
      const p = paramsFromInputs(),
        r = calculateStack(p);
      if (!r.count)
        throw new Error(
          "No complete sheet fits this budget. Increase the budget or reduce thickness.",
        );
      if (r.count > 500)
        throw new Error(
          "The 3D view supports at most 500 sheets. Reduce the budget or increase thickness.",
        );
      parameters = p;
      result = r;
      selected = Math.min(selected, result.count);
      const fresh = makeGeometry(parameters);
      if (geometry) geometry.dispose();
      geometry = fresh;
      for (const obj of [...stack.children]) {
        stack.remove(obj);
        obj.dispose?.();
      }
      steel = new THREE.InstancedMesh(geometry, steelMat, result.count);
      steel.name = "Individual_steel_sheets";
      lowerCoat = new THREE.InstancedMesh(geometry, coatMat, result.count);
      lowerCoat.name = "Lower_face_coatings";
      upperCoat = new THREE.InstancedMesh(geometry, coatMat, result.count);
      upperCoat.name = "Upper_face_coatings";
      stack.add(steel, lowerCoat, upperCoat);
      stack.userData = studyPayload(parameters);
      $("lam-error").hidden = true;
      document
        .querySelectorAll(".lam-export")
        .forEach((b) => (b.disabled = false));
      renderResults();
      positionLayers();
      fit();
    } catch (e) {
      $("lam-error").textContent =
        e.message + " The last valid model is retained.";
      $("lam-error").hidden = false;
      document
        .querySelectorAll(".lam-export")
        .forEach((b) => (b.disabled = true));
    }
  }
  for (const key of Object.keys(defaults)) {
    const el = $("lam-" + key);
    if (el) {
      el.value = defaults[key];
      el.addEventListener("change", rebuild);
    }
  }
  $("lam-spread").oninput = (e) => {
    spread = Number(e.target.value) / 100;
    positionLayers();
  };
  $("lam-spread").onchange = fit;
  $("lam-layer").oninput = (e) => {
    selected = Number(e.target.value);
    positionLayers();
  };
  $("lam-coating-visible").onchange = (e) => {
    coatingVisible = e.target.checked;
    positionLayers();
  };
  $("lam-view-mode").onchange = (e) => {
    viewMode = e.target.value;
    positionLayers();
    fit();
  };
  $("lam-fit").onclick = fit;
  $("lam-reset").onclick = () => {
    for (const [k, v] of Object.entries(defaults)) {
      const el = $("lam-" + k);
      if (el) el.value = v;
    }
    rebuild();
  };
  $("lam-export-json").onclick = () =>
    download(
      JSON.stringify(studyPayload(parameters), null, 2),
      "lamination-study.json",
      "application/json",
    );
  $("lam-export-dxf").onclick = () =>
    download(
      profileDXF(parameters),
      "provisional-lamination-mm.dxf",
      "application/dxf",
    );
  $("lam-export-glb").onclick = async () => {
    const button = $("lam-export-glb");
    button.disabled = true;
    button.textContent = "Exporting…";
    try {
      // Export true-size assembled geometry, not the display spread or a hidden-layer state.
      const exportGroup = new THREE.Group();
      exportGroup.name = "Provisional_lamination_stack";
      exportGroup.userData = studyPayload(parameters);
      const t = parameters.steel,
        c = parameters.coating / 1000,
        g = parameters.gap / 1000;
      for (let i = 0; i < result.count; i++) {
        const z = i * (t + 2 * c + g) - result.gross / 2;
        for (const [name, start, depth, mat] of [
          ["steel", z + c, t, steelMat],
          ["coating_lower", z, c, coatMat],
          ["coating_upper", z + c + t, c, coatMat],
        ]) {
          if (depth === 0) continue;
          const mesh = new THREE.Mesh(geometry, mat);
          mesh.name = `L${String(i + 1).padStart(3, "0")}_${name}`;
          mesh.scale.set(0.001, 0.001, depth * 0.001);
          mesh.position.z = start * 0.001;
          mesh.userData = { layer: i + 1, kind: name, thickness_mm: depth };
          exportGroup.add(mesh);
        }
      }
      const buffer = await new GLTFExporter().parseAsync(exportGroup, {
        binary: true,
      });
      download(buffer, "provisional-lamination-stack.glb", "model/gltf-binary");
    } catch (e) {
      $("lam-error").textContent = `Export failed: ${e.message}`;
      $("lam-error").hidden = false;
    } finally {
      button.disabled = false;
      button.textContent = "Stack GLB ↓";
    }
  };
  const ray = new THREE.Raycaster(),
    pointer = new THREE.Vector2();
  let down;
  renderer.domElement.addEventListener(
    "pointerdown",
    (e) => (down = [e.clientX, e.clientY]),
  );
  renderer.domElement.addEventListener("pointerup", (e) => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5)
      return;
    const r = renderer.domElement.getBoundingClientRect();
    pointer.set(
      ((e.clientX - r.left) / r.width) * 2 - 1,
      (-(e.clientY - r.top) / r.height) * 2 + 1,
    );
    ray.setFromCamera(pointer, camera);
    const hit = ray.intersectObjects(
      stack.children.filter((m) => m.visible),
      false,
    )[0];
    if (hit) {
      selected = hit.instanceId + 1;
      $("lam-layer").value = selected;
      positionLayers();
    }
  });
  const resize = () => {
    const w = viewport.clientWidth,
      h = viewport.clientHeight;
    if (!w || !h) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    if (result) fit();
    dirty = true;
  };
  new ResizeObserver(resize).observe(viewport);
  rebuild();
  resize();
  renderer.setAnimationLoop(() => {
    controls.update();
    if (dirty && !$("lamination-panel").hidden) {
      const distance = camera.position.distanceTo(controls.target);
      camera.near = Math.max(0.01, distance / 10);
      camera.far = Math.max(1000, distance * 10);
      camera.updateProjectionMatrix();
      renderer.render(scene, camera);
      dirty = false;
    }
  });
  window.__lamination = {
    getState: () => ({
      parameters: { ...parameters },
      result: { ...result },
      spread,
      selected,
      viewMode,
    }),
    scene,
    renderer,
    steel: () => steel,
    rebuild,
  };
}
