// Dimensioned 2D section diagram generated from the displayed geometry.
//
// The numbers are measured from the mesh actually on screen, not copied from a
// document, so a diagram cannot disagree with the model it describes.

const fmt = (v) => {
  const r = Math.round(v * 100) / 100;
  return Number.isInteger(r) ? String(r) : r.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
};

// Radius profile sampled from the mesh: for each z slice, the minimum and maximum
// radius present. This recovers bores, lands and flanges for any body of revolution.
function profile(mesh, slices = 40) {
  const geo = mesh.geometry;
  const pos = geo.attributes.position;
  const box = geo.boundingBox ?? (geo.computeBoundingBox(), geo.boundingBox);
  const z0 = box.min.z,
    z1 = box.max.z;
  const rows = [];
  const step = (z1 - z0) / slices;
  for (let i = 0; i <= slices; i++) {
    const z = z0 + i * step;
    const tol = step * 0.5 + 1e-6;
    let lo = Infinity,
      hi = 0;
    for (let v = 0; v < pos.count; v++) {
      const pz = pos.getZ(v);
      if (Math.abs(pz - z) > tol) continue;
      const r = Math.hypot(pos.getX(v), pos.getY(v));
      if (r > 1e-6) {
        lo = Math.min(lo, r);
        hi = Math.max(hi, r);
      }
    }
    if (hi > 0) rows.push([z, lo === Infinity ? 0 : lo, hi]);
  }
  return rows;
}

// Detect whether the mesh is a body of revolution about its own local Z axis.
function isRevolved(rows) {
  if (rows.length < 3) return false;
  const zs = rows.map((r) => r[0]);
  const heights = new Set(zs.map((z) => Math.round(z * 1e5)));
  return heights.size >= 3;
}

function dimensionLine(x1, y1, x2, y2) {
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="dim"/>`;
}

/**
 * Build a section diagram for one mesh.
 * units: mesh coordinates are metres; the diagram is in millimetres.
 */
export function sectionDiagram(meshes, label) {
  if (!meshes.length) return "";
  let box = null;
  const rows = [];
  for (const m of meshes) {
    m.geometry.computeBoundingBox();
    const b = m.geometry.boundingBox;
    box = box
      ? {
          min: {
            x: Math.min(box.min.x, b.min.x),
            y: Math.min(box.min.y, b.min.y),
            z: Math.min(box.min.z, b.min.z),
          },
          max: {
            x: Math.max(box.max.x, b.max.x),
            y: Math.max(box.max.y, b.max.y),
            z: Math.max(box.max.z, b.max.z),
          },
        }
      : b;
    rows.push(...profile(m));
  }
  if (!box) return "";
  const mm = (v) => v * 1000;
  const zLo = mm(box.min.z),
    zHi = mm(box.max.z);
  const rMax = mm(Math.max(box.max.x, box.max.y, -box.min.x, -box.min.y));
  const axial = zHi - zLo;
  const od = rMax * 2;

  // Merge sampled rows into a step profile: (z0, z1, rInner, rOuter).
  const steps = [];
  const sorted = rows.slice().sort((a, b) => a[0] - b[0]);
  for (const [z, lo, hi] of sorted) {
    const zm = mm(z);
    const cur = steps[steps.length - 1];
    const ri = mm(lo),
      ro = mm(hi);
    if (cur && Math.abs(cur.ro - ro) < 0.12 && Math.abs(cur.ri - ri) < 0.12) {
      cur.z1 = zm;
    } else {
      steps.push({ z0: zm, z1: zm, ri, ro });
    }
  }

  const W = 320,
    H = 200,
    padL = 30,
    padR = 30,
    padT = 34,
    padB = 28;
  const scale = Math.min(
    (W - padL - padR) / Math.max(axial, 1),
    (H - padT - padB) / Math.max(od, 1),
  );
  const cxs = padL + (W - padL - padR) / 2;
  const cys = padT + (H - padT - padB) / 2;
  const X = (z) => cxs + (z - (zLo + zHi) / 2) * scale;
  const Y = (r) => cys + r * scale;

  let paths = "";
  for (const s of steps) {
    const x0 = X(s.z0),
      x1 = X(s.z1),
      yi = Y(s.ri),
      yo = Y(s.ro);
    // upper half (mirrored across the axis) as a filled step
    paths += `<rect x="${x0}" y="${yo}" width="${Math.max(x1 - x0, 0.4)}" height="${Math.max(
      yi - yo,
      0.4,
    )}" class="solid"/>`;
    // lower half
    paths += `<rect x="${x0}" y="${Y(-s.ri) - Math.max(yi - yo, 0.4)}" width="${Math.max(
      x1 - x0,
      0.4,
    )}" height="${Math.max(yi - yo, 0.4)}" class="solid"/>`;
  }

  const axisY = Y(0);
  const dims = [];
  // overall axial dimension under the part
  const dy = H - 10;
  dims.push(dimensionLine(X(zLo), dy, X(zHi), dy));
  dims.push(dimensionLine(X(zLo), dy - 3, X(zLo), dy + 3));
  dims.push(dimensionLine(X(zHi), dy - 3, X(zHi), dy + 3));
  dims.push(
    `<text x="${(X(zLo) + X(zHi)) / 2}" y="${dy - 4}" class="dimtext">${fmt(axial)} mm</text>`,
  );
  // overall diameter on the right
  const dx = W - 8;
  dims.push(dimensionLine(dx, Y(-od / 2), dx, Y(od / 2)));
  dims.push(dimensionLine(dx - 3, Y(-od / 2), dx + 3, Y(-od / 2)));
  dims.push(dimensionLine(dx - 3, Y(od / 2), dx + 3, Y(od / 2)));
  dims.push(
    `<text x="${dx - 4}" y="${axisY + 3}" class="dimtext" text-anchor="end">Ø${fmt(od)}</text>`,
  );

  // Label the features that matter: the overall land, plus the largest distinct bores,
  // spread vertically so the text cannot collide.
  const byOuter = steps.slice().sort((a, b) => b.ro - a.ro);
  const seen = new Set();
  const picks = [];
  for (const s of byOuter) {
    const boreD = Math.round(s.ri * 2 * 100) / 100;
    if (boreD <= 0.4 || seen.has(boreD)) continue;
    seen.add(boreD);
    picks.push({ z: s.z0, boreD, ro: s.ro });
    if (picks.length >= 3) break;
  }
  picks.sort((a, b) => b.boreD - a.boreD);
  picks.forEach((p, i) => {
    const rows = [-0.62, 0.0, 0.62];
    const y = axisY + rows[i] * (H / 2 - padT) * 0.75;
    const anchorLeft = i % 2 === 0;
    const x = anchorLeft ? padL + 2 : W - padR - 2;
    dims.push(
      `<line x1="${x}" y1="${y}" x2="${X(p.z)}" y2="${y}" class="leader"/>` +
        `<text x="${x}" y="${y - 3}" class="dimtext" text-anchor="${
          anchorLeft ? "start" : "end"
        }">Ø${fmt(p.boreD)} bore</text>`,
    );
  });
  // overall land diameter, marked on the section itself
  const bigRo = byOuter[0].ro * 2;
  dims.push(
    `<text x="${padL + 2}" y="${padT - 20}" class="dimtext" text-anchor="start">Ø${fmt(
      bigRo,
    )} max</text>`,
  );
  // axial positions of the ends relative to the assembly origin
  dims.push(`<text x="${padL + 2}" y="${padT - 7}" class="dimtext" text-anchor="start">z ${fmt(zLo)}</text>`);
  dims.push(`<text x="${W - padR - 2}" y="${padT - 7}" class="dimtext" text-anchor="end">z ${fmt(zHi)}</text>`);

  return `<figure class="section-fig"><figcaption>${label}</figcaption>
<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Dimensioned axial section, millimetres">
  <line x1="${padL - 10}" y1="${axisY}" x2="${W - padR + 10}" y2="${axisY}" class="axis"/>
  ${paths}
  ${dims.join("\n  ")}
  <text x="6" y="${H - 6}" class="dimtext" text-anchor="start">section · mm</text>
</svg></figure>`;
}

export function hasDiagram(meshes) {
  return meshes.length > 0;
}

export { isRevolved, profile };
