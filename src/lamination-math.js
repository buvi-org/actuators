// All profile dimensions in mm. Coating/gap inputs in micrometres.
// This is an original provisional study, not recovered CubeMars lamination CAD.
export const defaults = Object.freeze({
  steel: 0.2,
  coating: 2,
  gap: 0,
  budget: 14,
  endAllowance: 0,
  steelTolerance: 0.005,
  coatingTolerance: 0.5,
  gapTolerance: 0,
  mode: "budget",
  count: 68,
  od: 80,
  bore: 60,
  rootDiameter: 68,
  slots: 36,
  toothWidth: 2.8,
  tipWidth: 4.8,
  tipDepth: 1.2,
});

export function validate(p) {
  for (const key of Object.keys(defaults).filter((k) => k !== "mode"))
    if (!Number.isFinite(p[key]))
      throw new Error(`${key} must be a finite number.`);
  if (!["budget", "count"].includes(p.mode))
    throw new Error("Choose a stack sizing mode.");
  if (p.steel < 0.05 || p.steel > 1)
    throw new Error("Steel thickness must be between 0.05 and 1 mm.");
  if (p.coating < 0 || p.coating > 100 || p.gap < 0 || p.gap > 100)
    throw new Error(
      "Coating and inter-sheet gap must be between 0 and 100 µm.",
    );
  if (
    p.budget <= 0 ||
    p.budget > 100 ||
    p.endAllowance < 0 ||
    p.endAllowance >= p.budget
  )
    throw new Error(
      "Stack budget must be 0–100 mm and exceed the end allowance.",
    );
  if (
    p.steelTolerance < 0 ||
    p.steelTolerance >= p.steel ||
    p.coatingTolerance < 0 ||
    p.gapTolerance < 0
  )
    throw new Error(
      "Thickness tolerances must be nonnegative; steel tolerance must be smaller than steel thickness.",
    );
  if (!Number.isInteger(p.count) || p.count < 1 || p.count > 500)
    throw new Error("Layer count must be an integer from 1 to 500.");
  if (!Number.isInteger(p.slots) || p.slots < 6 || p.slots > 96)
    throw new Error("Slot count must be an integer from 6 to 96.");
  if (!(
    p.bore > 0 &&
    p.bore < p.rootDiameter &&
    p.rootDiameter < p.od &&
    p.od <= 200
  ))
    throw new Error(
      "Profile needs 0 < bore < slot-root diameter < outside diameter ≤ 200 mm.",
    );
  if (!(p.tipDepth > 0 && p.tipDepth < (p.od - p.rootDiameter) / 2))
    throw new Error("Tip depth must be smaller than tooth radial height.");
  const r = p.rootDiameter / 2,
    neck = p.od / 2 - p.tipDepth;
  if (!(
    p.toothWidth > 0 &&
    p.tipWidth >= p.toothWidth &&
    p.toothWidth < 2 * r * Math.sin(Math.PI / p.slots) &&
    p.tipWidth < 2 * neck * Math.sin(Math.PI / p.slots)
  ))
    throw new Error(
      "Tooth widths must leave an open slot and tip width must be at least body width.",
    );
}

export function calculateStack(p) {
  validate(p);
  const t = p.steel,
    c = p.coating / 1000,
    g = p.gap / 1000,
    H = p.budget - p.endAllowance;
  const pitch = t + 2 * c;
  const count =
    p.mode === "count"
      ? p.count
      : Math.max(0, Math.floor((H + g + 1e-10) / (pitch + g)));
  const gross = count ? count * pitch + (count - 1) * g : 0,
    iron = count * t;
  const tmax = t + p.steelTolerance,
    cmax = (p.coating + p.coatingTolerance) / 1000,
    gmax = (p.gap + p.gapTolerance) / 1000;
  const tmin = t - p.steelTolerance,
    cmin = Math.max(0, p.coating - p.coatingTolerance) / 1000,
    gmin = Math.max(0, p.gap - p.gapTolerance) / 1000;
  const worstMax = count ? count * (tmax + 2 * cmax) + (count - 1) * gmax : 0;
  const worstMin = count ? count * (tmin + 2 * cmin) + (count - 1) * gmin : 0;
  const conservativeCount = Math.max(
    0,
    Math.floor((H + gmax + 1e-10) / (tmax + 2 * cmax + gmax)),
  );
  return {
    count,
    pitch,
    gross,
    iron,
    coatingTotal: count * 2 * c,
    gapTotal: Math.max(0, count - 1) * g,
    total: gross + p.endAllowance,
    remaining: H - gross,
    fillFactor: gross ? iron / gross : 0,
    worstMax,
    worstMin,
    conservativeCount,
    fits: count > 0 && gross <= H + 1e-9,
    worstFits: count > 0 && worstMax <= H + 1e-9,
  };
}

export function profilePoints(p) {
  validate(p);
  const R = p.od / 2,
    r = p.rootDiameter / 2,
    neck = R - p.tipDepth,
    half = Math.PI / p.slots;
  const bodyRoot = Math.asin(p.toothWidth / (2 * r)),
    bodyNeck = Math.asin(p.toothWidth / (2 * neck));
  const tipNeck = Math.asin(p.tipWidth / (2 * neck)),
    tipOuter = Math.asin(p.tipWidth / (2 * R));
  const points = [];
  const polar = (rad, a) => points.push([rad * Math.cos(a), rad * Math.sin(a)]);
  for (let i = 0; i < p.slots; i++) {
    const a = i * 2 * half;
    polar(r, a - half);
    polar(r, a - bodyRoot);
    polar(neck, a - bodyNeck);
    polar(neck, a - tipNeck);
    for (let j = 0; j <= 4; j++)
      polar(R, a - tipOuter + (2 * tipOuter * j) / 4);
    polar(neck, a + tipNeck);
    polar(neck, a + bodyNeck);
    polar(r, a + bodyRoot);
  }
  return points;
}

export function studyPayload(p) {
  return {
    schemaVersion: 1,
    kind: "provisional-lamination-study",
    manufacturerProfile: false,
    units: {
      dimensions: "mm",
      coating: "µm per face",
      gap: "µm per interface",
    },
    parameters: { ...p },
    results: calculateStack(p),
    profile: { outer: profilePoints(p), boreDiameter: p.bore },
    modelAssumptions: [
      "36 slots is published; all other profile dimensions and thicknesses are provisional.",
      "Each sheet has two coating faces. Optional gap is additional adhesive/void thickness between sheets.",
      "Both exterior coating faces are included. End allowance is added once outside the stack.",
      "Worst-case values assume all thicknesses simultaneously reach their tolerance bounds.",
      "Steel input excludes coating. Do not add coating again if a supplier thickness already includes it.",
      "No burr, compression, waviness or edge coating is included unless represented in the effective gap.",
    ],
  };
}

export function profileDXF(p) {
  const pts = profilePoints(p);
  const lines = [
    "0",
    "SECTION",
    "2",
    "HEADER",
    "9",
    "$INSUNITS",
    "70",
    "4",
    "0",
    "ENDSEC",
    "0",
    "SECTION",
    "2",
    "ENTITIES",
    "0",
    "LWPOLYLINE",
    "8",
    "PROVISIONAL_STEEL",
    "90",
    String(pts.length),
    "70",
    "1",
  ];
  for (const [x, y] of pts) lines.push("10", x.toFixed(7), "20", y.toFixed(7));
  lines.push(
    "0",
    "CIRCLE",
    "8",
    "PROVISIONAL_BORE",
    "10",
    "0",
    "20",
    "0",
    "30",
    "0",
    "40",
    (p.bore / 2).toFixed(7),
    "0",
    "ENDSEC",
    "0",
    "EOF",
  );
  return lines.join("\n") + "\n";
}
