import * as THREE from "three";
import { defaults, calculateStack, profilePoints } from "./lamination-math.js";

// Added geometry is an engineering illustration, never an OEM measurement.
export function buildAssembly(
  bom,
  manifest,
  driverInventory,
  sourceModel,
  housingSupports,
  sunSolid,
  planetSolid,
  ringSolid,
) {
  const nodes = new Map(),
    meshes = [],
    root = new THREE.Group();
  root.name = "Complete_engineering_study";
  root.add(sourceModel);
  const addNode = (id, name, parent, extra = {}) => {
    const n = { id, name, parent, children: [], ...extra };
    nodes.set(id, n);
    if (parent) nodes.get(parent).children.push(id);
    return n;
  };
  addNode("root", "AK80-9 / complete engineering study", null, {
    kind: "assembly",
  });
  for (const [id, name] of [
    ["stator", "Stator assembly"],
    ["rotor", "Rotor assembly"],
    ["transmission", "Planetary transmission"],
    ["bearings", "Bearings"],
    ["structure", "Housing & covers"],
    ["fasteners", "Fasteners"],
    ["electronics", "Electronics"],
    ["consumables", "Assembly materials"],
  ])
    addNode("group:" + id, name, "root", { kind: "assembly" });
  const group = {
    Motor: "stator",
    Transmission: "transmission",
    Bearings: "bearings",
    Structure: "structure",
    Fasteners: "fasteners",
    Electronics: "electronics",
    Consumables: "consumables",
  };
  const override = {
    EM03: "rotor",
    EM04: "rotor",
    G03: "rotor",
    C02: "rotor",
    EM05: "stator",
    EM06: "stator",
    E04: "stator",
  };
  // Parents precede their children in the engineering BOM.
  for (const row of bom)
    addNode(
      row.id,
      row.name,
      row.parent || "group:" + (override[row.id] || group[row.group]),
      { kind: "component", row, status: row.status },
    );
  const link = (mesh, id, offset = 0, kind = "provisional") => {
    mesh.userData.nodeId = id;
    mesh.userData.basePosition = mesh.position.clone();
    mesh.userData.explode = offset;
    mesh.userData.geometryKind = kind;
    mesh.name = id;
    meshes.push(mesh);
    return mesh;
  };
  sourceModel.traverse((mesh) => {
    if (!mesh.isMesh) return;
    let node = mesh,
      part;
    while (node && !part) {
      part = manifest.parts.find((p) => p.id === node.name);
      node = node.parent;
    }
    if (!part) return;
    if (part.bomId === "G02") {
      mesh.visible = false;
      return;
    }
    const id = `${part.bomId}/${part.id}`;
    addNode(id, `${part.name} · ${part.id}`, part.bomId, {
      kind: "instance",
      part,
      status: "Reference CAD",
      description:
        part.bomId === "F01"
          ? [
              "NAUO7",
              ...Array.from({ length: 7 }, (_, i) => "NAUO" + (22 + i)),
            ].includes(part.id)
            ? "Front joint: main housing M01 to fixed ring gear / stator radial locator G05, eight screws on 54 mm PCD. Candidate thread M2.5 x 0.45; nominal screw penetration 3.3 mm. Thread strength and tightening torque pending."
            : "Rear joint: rear housing M02 to main housing M01, sixteen source screws. Thread engagement and tightening torque require validation."
          : undefined,
    });
    mesh.material = mesh.material.clone();
    mesh.material.color.set(part.color);
    mesh.material.metalness = 0.42;
    mesh.material.roughness = 0.4;
    mesh.material.envMapIntensity = 0.75;
    mesh.material.side = THREE.DoubleSide;
    link(mesh, id, part.explode, "reference");
  });
  const replacedMeshes = [];
  sourceModel.traverse((m) => {
    if (m.isMesh && !m.userData.nodeId) replacedMeshes.push(m);
  });
  replacedMeshes.forEach((m) => m.removeFromParent());
  if (housingSupports) {
    addNode(
      "M01/boss-extensions",
      "Primeform R2 - housing stator stop and screw bosses",
      "M01",
      {
        kind: "instance",
        status: "Primeform modification - clearance conflict",
        description:
          "Choice C: housing stator seat at z 11.436 mm, radii 30.1 to 33.5 mm, plus sixteen 5 mm screw supports extended to the housing floors; 16 existing screw bores retained. Added supports intersect the current provisional rotor yoke. Resolve rotor/housing envelopes before manufacture. Toggle this item off to inspect the original CubeMars housing.",
      },
    );
    root.add(housingSupports);
    housingSupports.traverse((mesh) => {
      if (!mesh.isMesh) return;
      mesh.material = new THREE.MeshStandardMaterial({
        color: "#b68b52",
        metalness: 0.4,
        roughness: 0.45,
        side: THREE.DoubleSide,
      });
      link(mesh, "M01/boss-extensions", 0, "provisional");
    });
  }
  const material = (color, opacity = 1) =>
    new THREE.MeshStandardMaterial({
      color,
      metalness: 0.35,
      roughness: 0.45,
      transparent: opacity < 1,
      opacity,
      depthWrite: opacity === 1,
      side: THREE.DoubleSide,
    });
  const add = (
    id,
    name,
    parent,
    geometry,
    color,
    position = [0, 0, 0],
    offset = 0,
    description = "",
    opacity = 1,
  ) => {
    addNode(id, name, parent, {
      kind: "instance",
      status: "Provisional illustration",
      description,
    });
    const mesh = new THREE.Mesh(geometry, material(color, opacity));
    mesh.position.set(...position.map((v) => v / 1000));
    root.add(mesh);
    link(mesh, id, offset);
    return mesh;
  };
  const ring = (inner, outer, height) => {
    const s = new THREE.Shape();
    s.absarc(0, 0, outer / 1000, 0, Math.PI * 2, false);
    if (inner) {
      const h = new THREE.Path();
      h.absarc(0, 0, inner / 1000, 0, Math.PI * 2, true);
      s.holes.push(h);
    }
    const g = new THREE.ExtrudeGeometry(s, {
      depth: height / 1000,
      bevelEnabled: false,
      curveSegments: 96,
    });
    g.translate(0, 0, -height / 2000);
    return g;
  };
  const box = (x, y, z) => new THREE.BoxGeometry(x / 1000, y / 1000, z / 1000);
  const annular = (
    id,
    parent,
    name,
    ri,
    ro,
    h,
    z,
    color,
    offset,
    description,
    opacity = 1,
  ) =>
    add(
      id,
      name,
      parent,
      ring(ri, ro, h),
      color,
      [0, 0, z],
      offset,
      description,
      opacity,
    );
  const p = { ...defaults },
    stack = calculateStack(p),
    outline = profilePoints(p),
    shape = new THREE.Shape(
      outline.map(([x, y]) => new THREE.Vector2(x / 1000, y / 1000)),
    );
  const hole = new THREE.Path();
  hole.absarc(0, 0, p.bore / 2000, 0, Math.PI * 2, true);
  shape.holes.push(hole);
  const layerGeo = new THREE.ExtrudeGeometry(shape, {
    depth: p.steel / 1000,
    bevelEnabled: false,
    curveSegments: 64,
  });
  const coatGeo = new THREE.ExtrudeGeometry(shape, {
    depth: p.coating / 1e6,
    bevelEnabled: false,
    curveSegments: 64,
  });
  addNode("EM01/steel", "Individual steel laminations (68)", "EM01", {
    kind: "assembly",
  });
  addNode("EM01/coating", "Insulation coating faces (136)", "EM01", {
    kind: "assembly",
  });
  for (let i = 0; i < stack.count; i++) {
    const tag = String(i + 1).padStart(3, "0"),
      z = 4.5 - stack.gross / 2 + i * stack.pitch;
    add(
      `EM01/L${tag}`,
      `Lamination ${i + 1} · 0.200 mm`,
      "EM01/steel",
      layerGeo,
      "#81929f",
      [0, 0, z + p.coating / 1000],
      -0.05,
      `Sheet ${i + 1}/${stack.count}; 36-slot provisional profile; OD 80 / bore 60 mm; slot root 68 mm; back iron 4 mm; steel 0.200 mm. Not recovered from manufacturer CAD.`,
    );
    for (const [face, dz] of [
      ["lower", 0],
      ["upper", p.coating / 1000 + p.steel],
    ])
      add(
        `EM01/L${tag}/${face}`,
        `Sheet ${i + 1} · ${face} coating · 2 µm`,
        "EM01/coating",
        coatGeo,
        "#5f9f94",
        [0, 0, z + dz],
        -0.05,
        "Study coating: 2 µm per face; chemistry and OEM thickness unknown.",
      );
  }
  annular(
    "EM03/yoke",
    "EM03",
    "Rotor magnetic yoke",
    42.5,
    45.5,
    15,
    0,
    "#596576",
    -0.018,
    "Illustrative steel yoke: ID 85, OD 91, length 15 mm. Material and OEM dimensions unknown.",
  );
  annular(
    "EM03/endbell",
    "EM03",
    "Rotor end bell",
    23,
    45.5,
    1,
    -8.1,
    "#46596a",
    -0.018,
    "Known interference: this provisional disc overlaps rear housing NAUO4 by approximately 2666.283 mm3 in assembled coordinates. A forward translation also conflicts with the present stator/winding envelope. Axial layout must be redesigned.",
  );
  const sectors = 42;
  for (let i = 0; i < sectors; i++) {
    const a = (i * 2 * Math.PI) / sectors,
      width = ((2 * Math.PI) / sectors) * 0.85,
      s = new THREE.Shape();
    s.absarc(0, 0, 0.0425, a - width / 2, a + width / 2, false);
    s.absarc(0, 0, 0.0405, a + width / 2, a - width / 2, true);
    s.closePath();
    const geo = new THREE.ExtrudeGeometry(s, {
      depth: 0.014,
      bevelEnabled: false,
      curveSegments: 12,
    });
    add(
      `EM04/magnet-${i + 1}`,
      `Magnet ${i + 1} · ${i % 2 ? "S" : "N"} inward`,
      "EM04",
      geo,
      i % 2 ? "#a9646b" : "#7195ad",
      [0, 0, -7],
      -0.018,
      "42 segments is a study assumption: the published 21 pole pairs establishes 42 poles, not the physical magnet-piece count. Arc coverage 85%, radial thickness 2 mm, length 14 mm are illustrative.",
    );
  }
  const coilShape = new THREE.Shape();
  coilShape.moveTo(-0.0023, -0.0078);
  coilShape.lineTo(0.0023, -0.0078);
  coilShape.lineTo(0.0023, 0.0078);
  coilShape.lineTo(-0.0023, 0.0078);
  coilShape.closePath();
  const coilHole = new THREE.Path();
  coilHole.moveTo(-0.0016, -0.00705);
  coilHole.lineTo(-0.0016, 0.00705);
  coilHole.lineTo(0.0016, 0.00705);
  coilHole.lineTo(0.0016, -0.00705);
  coilHole.closePath();
  coilShape.holes.push(coilHole);
  const coilGeo = new THREE.ExtrudeGeometry(coilShape, {
    depth: 0.0045,
    bevelEnabled: false,
  });
  for (let i = 0; i < 36; i++) {
    const a = (i * Math.PI * 2) / 36,
      radial = new THREE.Vector3(Math.cos(a), Math.sin(a), 0),
      tangent = new THREE.Vector3(-Math.sin(a), Math.cos(a), 0);
    const coil = add(
      `EM02/coil-${i + 1}`,
      `Tooth coil ${i + 1}`,
      "EM02",
      coilGeo,
      ["#c27b40", "#e0a354", "#a65a34"][i % 3],
      [34.5 * Math.cos(a), 34.5 * Math.sin(a), 4.5],
      -0.05,
      "Winding bundle placeholder, not a turn-by-turn winding. Actual turns, conductor size, coil pitch and phase sequence remain unknown; colour is only visual grouping.",
    );
    coil.setRotationFromMatrix(
      new THREE.Matrix4().makeBasis(
        tangent,
        new THREE.Vector3(0, 0, 1),
        radial,
      ),
    );
    const liner = add(
      `EM05/liner-${i + 1}`,
      `Tooth insulation ${i + 1}`,
      "EM05",
      box(4.5, 3.15, 14.1),
      "#ded5ad",
      [36.75 * Math.cos(a), 36.75 * Math.sin(a), 4.5],
      -0.05,
      "Solid envelope proxy for slot insulation, not a validated liner thickness or cut pattern.",
      0.25,
    );
    liner.rotation.z = a;
  }
  annular(
    "EM06/varnish",
    "EM06",
    "Impregnation extent (schematic)",
    34.5,
    39.5,
    0.15,
    12.4,
    "#dac57d",
    -0.05,
    "Illustrative end-winding impregnation extent; not a material fill volume or quantity.",
    0.25,
  );
  const solidGeometry = (scene) => {
    let geometry;
    scene.traverse((mesh) => {
      if (mesh.isMesh) geometry = mesh.geometry;
    });
    return geometry;
  };
  root.add(sunSolid);
  sunSolid.traverse((mesh) => {
    if (!mesh.isMesh) return;
    mesh.material = material("#d6a75e");
    mesh.position.z = 0.00825;
    link(mesh, "G02", 0.055);
  });
  nodes.get("G02").status = "Provisional gear-and-shaft solid";
  nodes.get("G02").description =
    "One connected gear-and-shaft solid: source end journals retained; central section z 3.75-11.25 mm replaced with the 20-tooth, module 0.3, 20 degrees involute candidate. Face width 7.5 mm. Circular root fillets 0.06 mm; nominal circular backlash 0.020 mm per mesh. Manufacturing release pending process, tolerances and strength verification. Viewer mesh is tessellated directly from the STEP solid.";
  for (let i = 0; i < 3; i++) {
    const a = (i * 2 * Math.PI) / 3,
      x = 13.5 * Math.cos(a),
      y = 13.5 * Math.sin(a);
    const planet = add(
      `G04/planet-${i + 1}`,
      `Planet gear ${i + 1}`,
      "G04",
      solidGeometry(planetSolid),
      "#b6bac4",
      [x, y, 8.25],
      0.055,
      "70-tooth involute candidate, module 0.3, 20 degrees pressure angle, 5 mm face width. STEP-derived mesh. Circular root fillets and backlash are candidate values; process and strength release pending.",
    );
    planet.rotation.z = a + Math.PI + Math.PI / 70 + (20 / 70) * a;
    add(
      `G06/pin-${i + 1}`,
      `Planet pin ${i + 1}`,
      "G06",
      ring(0, 2.5, 8),
      "#bdc7d4",
      [x, y, 8.75],
      0.065,
      "Illustrative pin diameter 5 mm. Count inferred from three-planet illustration; material, retention and fit unknown.",
    );
    add(
      `G07/bearing-${i + 1}`,
      `Planet bearing ${i + 1}`,
      "G07",
      ring(2.5, 3, 5),
      "#78939a",
      [x, y, 8.25],
      0.055,
      "Annular planet-bearing/bushing placeholder; actual bearing architecture and size unresolved.",
    );
  }
  const ringMesh = new THREE.Mesh(
    solidGeometry(ringSolid),
    material("#aeb8c7"),
  );
  ringMesh.position.z = 0.00825;
  ringMesh.rotation.z = Math.PI / 160;
  root.add(ringMesh);
  link(ringMesh, "G05", 0.045);
  nodes.get("G05").description =
    "160-tooth internal involute candidate, module 0.3, 20 degrees pressure angle, 5 mm face width. One STEP-derived solid. With ring fixed, sun input and carrier output, ratio is exactly 1 + 160/20 = 9. Manufacturing release pending. Compact OD 59.96 mm rim has eight M2.5 tapped positions on 54 mm PCD; ring OD locates the 60 mm stator bore radially. Main housing seats stator at z=11.436 mm. Long sleeve removed. This stationary carrier is a Primeform proposal, not recovered OEM geometry.";
  add(
    "E03/sensor",
    "Magnetic encoder package",
    "E03",
    box(4, 4, 1),
    "#222a37",
    [0, 0, -13.7],
    -0.078,
    "Illustrative sensor package/location; exact IC and footprint unknown.",
  );
  add(
    "E04/ntc",
    "Winding NTC",
    "E04",
    new THREE.SphereGeometry(0.0011, 16, 12),
    "#d89b6b",
    [36, 0, 10.5],
    -0.05,
    "MF51B 103F3950 is published. Bead shape and placement are illustrative.",
  );
  add(
    "E05/connector",
    "Power/CAN connector envelope",
    "E05",
    box(9, 7, 6),
    "#252831",
    [30, -8, -16],
    -0.075,
    "Connector function and mating names from manual; this placement/envelope is illustrative.",
  );
  add(
    "E06/connector",
    "UART connector envelope",
    "E06",
    box(5, 4, 3),
    "#e5e0ce",
    [29, 6, -16],
    -0.075,
    "CJT three-pin connector; geometry and placement provisional.",
  );
  for (let i = 0; i < 6; i++)
    add(
      `E07/switch-${i + 1}`,
      `Power-switch package ${i + 1}`,
      "E07",
      box(5, 6, 1),
      "#263138",
      [17 * Math.cos((i * Math.PI) / 3), 17 * Math.sin((i * Math.PI) / 3), -14],
      -0.075,
      "Six-switch topology illustration, not identification of the 12 Q-designators in the source board.",
    );
  add(
    "E08/control",
    "Control electronics envelope",
    "E08",
    box(10, 10, 1.2),
    "#263138",
    [-10, 5, -14],
    -0.075,
    "Illustrative MCU/control region. Exact placement, netlist and device are not established.",
  );
  add(
    "E09/capacitor",
    "Bulk capacitor envelope",
    "E09",
    ring(0, 4, 9),
    "#577279",
    [-21, -13, -18],
    -0.09,
    "Placeholder only: capacitance, size, position and whether a separate capacitor is needed are unknown.",
  );
  annular(
    "C01/grease",
    "C01",
    "Lubrication extent",
    4,
    24,
    0.2,
    12.2,
    "#c4c19a",
    0.055,
    "Schematic lubrication region only; not a grease-volume estimate.",
    0.18,
  );
  annular(
    "C02/bond",
    "C02",
    "Magnet bondline (study)",
    42.45,
    42.5,
    14,
    0,
    "#d2ac69",
    -0.018,
    "50 µm radial bondline assumed for display; chemistry and actual thickness unknown.",
  );
  annular(
    "C03/interface",
    "C03",
    "Stator retaining bondline (study)",
    29.98,
    30,
    5.686,
    8.593,
    "#78c6ba",
    -0.05,
    "Proposed 0.020 mm radial retaining-adhesive bondline between stator bore and compact ring OD; housing shoulder is axial stop. Adhesive grade, bond strength and thermal performance must be validated.",
  );
  const seal = new THREE.TorusGeometry(0.046, 0.00045, 10, 100);
  add(
    "C04/seal",
    "Seal / retention allowance",
    "C04",
    seal,
    "#344d48",
    [0, 0, 7],
    0.008,
    "Representative seal only, not evidence that the OEM actuator includes this seal or has an IP rating.",
  );
  addNode("E01/inventory", "Electronic reference designators (205)", "E01", {
    kind: "assembly",
    description:
      "Source package inventory. Individual board positions are not mapped to the actuator mesh; entries remain selectable data records.",
  });
  for (const item of driverInventory.components)
    addNode(
      `pcb:${item.reference}`,
      `${item.reference} · ${item.category}`,
      "E01/inventory",
      { kind: "electronic", electronic: item, status: "Driver STEP inventory" },
    );
  return { root, nodes, meshes, studyParameters: p };
}

export function belongsTo(nodes, id, ancestor) {
  let n = nodes.get(id);
  while (n) {
    if (n.id === ancestor) return true;
    n = nodes.get(n.parent);
  }
  return false;
}
export function inheritedHidden(nodes, id, hidden) {
  let n = nodes.get(id);
  while (n) {
    if (hidden.has(n.id)) return true;
    n = nodes.get(n.parent);
  }
  return false;
}
