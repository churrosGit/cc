// Cut-away 3D models for the keyboard comparison loop (three.js 0.165). Units: millimetres.
// World axes: x = along the key row, y = up, z = toward the camera. The cut plane is z = 0:
// static parts (housing, plates, sheets, keycaps) keep only their back half (z <= 0) so the section
// faces show; the moving core parts (stem, spring, contact leaves, plunger) stay whole.
import * as THREE from 'three';

export const PITCH = 19.05;                          // standard key pitch
const V2 = (x, y) => new THREE.Vector2(x, y);
const shadowed = m => { m.traverse(o => { if (o.isMesh) o.castShadow = o.receiveShadow = true; }); return m; };

// XY profile extruded along z from z1 to z2
export function prism(pts, z1, z2, mat, curve = 24) {
  const geo = new THREE.ExtrudeGeometry(new THREE.Shape(pts.map(p => V2(p[0], p[1]))), { depth: z2 - z1, bevelEnabled: false, curveSegments: curve });
  geo.translate(0, 0, z1);
  return shadowed(new THREE.Mesh(geo, mat));
}
export const box = (x1, x2, y1, y2, z1, z2, mat) => prism([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], z1, z2, mat);

// horizontal slab from an outline given in (x, z) world coords, between heights y1..y2
export function slab(ptsXZ, y1, y2, mat) {
  const geo = new THREE.ExtrudeGeometry(new THREE.Shape(ptsXZ.map(p => V2(p[0], -p[1]))), { depth: y2 - y1, bevelEnabled: false, curveSegments: 48 });
  geo.rotateX(-Math.PI / 2); geo.translate(0, y1, 0);
  return shadowed(new THREE.Mesh(geo, mat));
}
// back-half rectangle x∈[-W,W], z∈[-D,0] with semicircular notches of radius r at each key centre on the cut edge
export function notchedOutline(W, D, keys, r, n = 40) {
  const pts = [[-W, 0]];
  for (const xk of keys) { for (let i = 0; i <= n; i++) { const a = Math.PI - Math.PI * i / n; pts.push([xk + r * Math.cos(a), -r * Math.sin(a)]); } }
  pts.push([W, 0], [W, -D], [-W, -D]);
  return pts;
}

// solid of revolution about the y axis, back half only, with the two section faces capped.
// profile: closed list of [r, y] (r >= 0)
export function halfLathe(profile, mat, seg = 48) {
  const g = new THREE.Group();
  const pts = profile.map(p => V2(Math.max(p[0], 1e-4), p[1]));
  const lathe = new THREE.LatheGeometry([...pts, pts[0]], seg, Math.PI / 2, Math.PI);
  g.add(new THREE.Mesh(lathe, mat));
  for (const s of [1, -1]) {
    const sh = new THREE.ShapeGeometry(new THREE.Shape(profile.map(p => V2(s * p[0], p[1]))));
    const cap = new THREE.Mesh(sh, mat); g.add(cap);
  }
  return shadowed(g);
}
export function updateHalfLathe(g, profile, seg = 48) {
  const pts = profile.map(p => V2(Math.max(p[0], 1e-4), p[1]));
  g.children[0].geometry.dispose(); g.children[0].geometry = new THREE.LatheGeometry([...pts, pts[0]], seg, Math.PI / 2, Math.PI);
  for (const [i, s] of [[1, 1], [2, -1]]) {
    g.children[i].geometry.dispose(); g.children[i].geometry = new THREE.ShapeGeometry(new THREE.Shape(profile.map(p => V2(s * p[0], p[1]))));
  }
}
const ring = (r1, r2, y1, y2) => [[r1, y1], [r2, y1], [r2, y2], [r1, y2]];

// keycap: tapered shell, back half, with a socket that takes the stem. y0 = skirt bottom.
// sock: 'cross' (two walls hugging a cross stem) or 'none'
export function keycap(mat, y0, { h = 6.6, sock = 'cross' } = {}) {
  const g = new THREE.Group(), top = y0 + h, ceil = top - 1.2;
  const outer = [[-9, y0], [-6.6, top], [6.6, top], [9, y0]];
  const shell = [...outer, [8, y0], [5.8, ceil], [-5.8, ceil], [-8, y0]];
  const taper = geo => {                                 // narrow toward the top in z as well (frustum)
    const p = geo.attributes.position;
    for (let i = 0; i < p.count; i++) { const f = 1 - 0.27 * (p.getY(i) - y0) / h; p.setZ(i, p.getZ(i) * f); }
    geo.computeVertexNormals(); return geo;
  };
  const s = prism(shell, -9, 0, mat); taper(s.geometry); g.add(s);
  const back = prism([[-8, y0], [-5.8, ceil], [5.8, ceil], [8, y0]], -9, -8, mat); taper(back.geometry); g.add(back);
  if (sock === 'cross') for (const sx of [-1, 1]) g.add(box(sx * 2.0, sx * 2.8, y0 + 1.6, ceil + 0.01, -2.8, 0, mat));
  return shadowed(g);
}

// ---------------------------------------------------------------------------------------------
// Membrane (rubber dome) keyboard. y = 0 is the top of the steel back plate.
//   bottom film 0–0.3 · spacer 0.3–0.6 (hole r 3.2) · top film 0.6–0.9 · dome sheet 0.9–1.4
//   dome rises to 5.4 · top case 6.6–8.0 with guide barrels 5.8–8.0 · keycap skirt at 12.0
export const MEM = { travel: 3.4, padGap: 3.1, film: 0.3 };
export function membraneBoard(M, { keys = [-PITCH, 0, PITCH], W = 40, D = 12 } = {}) {
  const g = new THREE.Group(), parts = { keys: [] };
  g.add(box(-W, W, -3.5, -1.0, -D, 0, M.caseM));                         // bottom case
  g.add(box(-W, W, -1.0, 0, -D, 0, M.plate));                            // steel back plate
  g.add(box(-W, W, 0, 0.3, -D, 0, M.film));                              // bottom film
  g.add(slab(notchedOutline(W, D, keys, 3.2), 0.3, 0.6, M.spacer));      // spacer with holes
  // top film: finely gridded so it can dimple into the spacer hole
  const tf = new THREE.BoxGeometry(2 * W, 0.3, D, 320, 1, 48); tf.translate(0, 0.75, -D / 2);
  const topFilm = shadowed(new THREE.Mesh(tf, M.film)); g.add(topFilm);
  topFilm.userData.base = Float32Array.from(tf.attributes.position.array);
  g.add(slab(notchedOutline(W, D, keys, 4.9), 0.9, 1.4, M.rubber));      // one rubber sheet for every key
  g.add(slab(notchedOutline(W, D, keys, 1.9), 6.6, 8.0, M.caseM));       // top case
  for (const xk of keys) {
    const k = {};
    const padB = halfLathe(ring(0, 2.6, 0.3, 0.38), M.pad); padB.position.x = xk; g.add(padB); k.padB = padB;
    const padT = halfLathe(ring(0, 2.6, 0.52, 0.6), M.pad); padT.position.x = xk; g.add(padT); k.padT = padT;
    const dome = halfLathe(domeProfile(0), M.rubber, 56); dome.position.x = xk; g.add(dome); k.dome = dome;
    const carbon = halfLathe(ring(0, 1.6, 0, 0.25), M.carbon); carbon.position.set(xk, 4.0, 0); g.add(carbon); k.carbon = carbon;
    const barrel = halfLathe(ring(1.9, 2.7, 5.8, 8.0), M.caseM); barrel.position.x = xk; g.add(barrel);
    const mover = new THREE.Group(); mover.position.x = xk; g.add(mover); k.mover = mover;
    mover.add(keycap(M.cap, 12.0, { sock: 'none' }));
    mover.add(halfLathe(ring(0, 1.6, 5.4, 17.45), M.plunger));
    parts.keys.push(k);
  }
  // press p (0..travel) of key i
  const setPress = (i, p) => {
    const k = parts.keys[i], xk = keys[i];
    k.mover.position.y = -p;
    updateHalfLathe(k.dome, domeProfile(p), 56); k.carbon.position.y = 4.0 - p;
    const defl = Math.min(MEM.film, Math.max(0, p - MEM.padGap));        // carbon pad pushes the top film down
    k.padT.position.y = -defl;
    const pos = tf.attributes.position, base = topFilm.userData.base;
    for (let v = 0; v < pos.count; v++) {
      const x = base[3 * v] - xk, z = base[3 * v + 2], r = Math.hypot(x, z);
      if (Math.abs(x) > 4) continue;
      const f = r < 3.2 ? (1 - (r / 3.2) ** 2) ** 2 : 0;
      pos.setY(v, base[3 * v + 1] - defl * Math.min(1, f * 1.35));
    }
    pos.needsUpdate = true; tf.computeVertexNormals();
    return defl >= MEM.film - 1e-3;                                       // films touch -> key registered
  };
  g.userData = { parts, setPress };
  return g;
}
// rubber dome cross-section for press p: conical wall buckles outward while keeping its length
function domeProfile(p) {
  const top = 5.4 - p, base = [5.5, 1.4], sh = [2.8, top], L0 = Math.hypot(2.7, 4.0);
  const c = Math.hypot(sh[0] - base[0], sh[1] - base[1]);
  const s = Math.sqrt(Math.max(0, 3 * c * (L0 - c) / 8));
  const dx = (sh[0] - base[0]) / c, dy = (sh[1] - base[1]) / c, nx = -dy, ny = dx;   // normal pointing outward/up
  const n = nx < 0 ? [-nx, -ny] : [nx, ny];
  const ctrl = [(base[0] + sh[0]) / 2 + 2 * s * n[0], (base[1] + sh[1]) / 2 + 2 * s * n[1]];
  const bez = (a, b, cc, t) => [(1 - t) ** 2 * a[0] + 2 * (1 - t) * t * cc[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * cc[1] + t * t * b[1]];
  const outer = [], inner = [], N = 18, th = 0.85;
  for (let i = 0; i <= N; i++) outer.push(bez(sh, base, ctrl, i / N));                   // shoulder -> base
  for (let i = 0; i <= N; i++) { const q = bez(base, sh, ctrl, i / N); inner.push([q[0] - th, q[1] - (i === N ? 0.8 : 0)]); }
  inner[0][1] = base[1];
  return [[0, top], [2.8, top], ...outer.slice(1), [base[0] - th, base[1]], ...inner.slice(1, -1), [2.1, top - 0.8], [1.6, top - 0.8], [1.6, top - 1.15], [0, top - 1.15]];
}

// ---------------------------------------------------------------------------------------------
// Mechanical switch on a PCB + steel plate. y = 0 is the PCB top.
//   housing floor 0–1 · centre post to 4 · plate 5–6.5 · top housing to 11.6 · keycap skirt at 11.0
// Contact leaves sit on the left (x ≈ −5); the stem's leg holds the moving leaf open until ~2 mm.
export const MECH = { travel: 4.0, legFace: -3.6, legNarrow: -2.9, legTop: 9.0, chamfer: 0.4, fingerY: 7.0, tipRest: -3.6, tipFree: -3.13, pivot: [-5.8, 1.0] };
export function mechBoard(M, { keys = [-PITCH, 0, PITCH], W = 40, D = 12 } = {}) {
  const g = new THREE.Group(), parts = { keys: [] };
  g.add(box(-W, W, -4.6, -1.6, -D, 0, M.caseM));                        // bottom case
  g.add(box(-W, W, -1.6, 0, -D, 0, M.pcb));                              // PCB
  // plate with a square hole per switch
  const hole = 7.0, plateOutline = [[-W, 0]];
  for (const xk of keys) plateOutline.push([xk - hole, 0], [xk - hole, -hole], [xk + hole, -hole], [xk + hole, 0]);
  plateOutline.push([W, 0], [W, -D], [-W, -D]);
  g.add(slab(plateOutline, 5.0, 6.5, M.plate));
  for (const xk of keys) {
    const k = {}, sw = new THREE.Group(); sw.position.x = xk; g.add(sw);
    // bottom housing: floor, walls through the plate, centre post
    sw.add(box(-7, 7, 0, 1.0, -7, 0, M.housing));
    for (const s of [-1, 1]) sw.add(box(s * 6.2, s * 7, 1.0, 6.5, -7, 0, M.housing));
    sw.add(box(-7, 7, 0, 6.5, -7, -6.2, M.housing));
    const post = halfLathe(ring(0, 1.6, 1.0, 4.0), M.housing); sw.add(post);
    // top housing (two section halves around the stem slot) + back wall
    const L = [[-7.8, 6.5], [-7.8, 7.3], [-5.4, 11.6], [-2.8, 11.6], [-2.8, 10.6], [-5.0, 10.6], [-7.0, 7.6], [-7.0, 6.5]];
    sw.add(prism(L, -7.8, 0, M.housing)); sw.add(prism(L.map(([x, y]) => [-x, y]), -7.8, 0, M.housing));
    sw.add(prism([[-7.0, 6.5], [-7.0, 7.6], [-5.0, 10.6], [5.0, 10.6], [7.0, 7.6], [7.0, 6.5]], -7.8, -7.0, M.housing));
    // contact leaves (z −1.4 … −0.2): stationary leaf + moving leaf on a pivot near its root
    const fixedLeaf = new THREE.Group(); sw.add(fixedLeaf);
    fixedLeaf.add(box(-5.15, -4.85, -3.2, 6.0, -1.4, -0.2, M.leaf));
    const solder = halfLathe([[0, -1.6], [0.9, -1.6], [0.25, -3.0], [0, -3.0]], M.solder); solder.position.x = -5.0; sw.add(solder);
    fixedLeaf.add(box(-5.95, -5.65, -3.2, 1.0, -1.4, -0.2, M.leaf));      // moving leaf root (fixed part)
    const solder2 = solder.clone(); solder2.position.x = -5.8; sw.add(solder2);
    const piv = new THREE.Group(); piv.position.set(...MECH.pivot, 0); sw.add(piv);
    const leafArm = new THREE.Group(); leafArm.position.set(-MECH.pivot[0], -MECH.pivot[1], 0); piv.add(leafArm);
    leafArm.add(box(-5.95, -5.65, 1.0, 7.15, -1.4, -0.2, M.leaf));
    leafArm.add(box(-5.65, -5.5, 5.2, 5.8, -1.4, -0.2, M.leaf));            // contact bump
    leafArm.add(box(-5.95, -3.75, 6.85, 7.15, -1.4, -0.2, M.leaf));         // finger
    const tip = shadowed(new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 1.2, 16), M.leaf));
    tip.rotation.x = Math.PI / 2; tip.position.set(-3.75, 7.0, -0.8); leafArm.add(tip);
    k.leaves = [fixedLeaf, leafArm]; k.piv = piv;
    // stem (whole): leg + body + shaft + cross
    const stem = new THREE.Group(); sw.add(stem); k.stem = stem;
    stem.add(prism([[-2.6, 6.6], [-3.6, 6.6], [-3.6, 8.6], [-2.9, 9.0], [-2.9, 10.0], [-2.6, 10.0]], -1.6, 1.0, M.stem));
    stem.add(box(-2.6, 2.6, 8.6, 10.6, -2.6, 2.6, M.stem));
    stem.add(box(-2.4, 2.4, 10.6, 12.4, -2.0, 2.0, M.stem));
    stem.add(box(-2.0, 2.0, 12.4, 16.4, -0.6, 0.6, M.stem));
    stem.add(box(-0.6, 0.6, 12.4, 16.4, -2.0, 2.0, M.stem));
    // spring (whole), rebuilt as it compresses
    const spring = shadowed(new THREE.Mesh(springGeo(8.6 - 1.0), M.spring)); spring.position.y = 1.0; sw.add(spring); k.spring = spring;
    // keycap
    const cap = keycap(M.cap, 11.0); stem.add(cap);
    parts.keys.push(k);
  }
  // returns true while the contacts touch
  const setPress = (i, p) => {
    const k = parts.keys[i];
    k.stem.position.y = -p;
    k.spring.geometry.dispose(); k.spring.geometry = springGeo(8.6 - p - 1.0);
    const yrel = MECH.fingerY + p, c0 = MECH.legTop - MECH.chamfer;
    const face = yrel < c0 ? MECH.legFace : yrel < MECH.legTop ? MECH.legFace + (MECH.legNarrow - MECH.legFace) * (yrel - c0) / MECH.chamfer : MECH.legNarrow;
    const tipX = Math.min(MECH.tipFree, face), dx = tipX - MECH.tipRest;
    k.piv.rotation.z = -dx / (MECH.fingerY - MECH.pivot[1]);
    return tipX >= MECH.tipFree - 1e-6;
  };
  g.userData = { parts, setPress };
  return g;
}
function springGeo(len, r = 2.3, wire = 0.22, turns = 6.5) {
  const pts = [], N = Math.round(turns * 36), l = len - 2 * wire;
  for (let i = 0; i <= N; i++) {
    const t = i / N, a = t * turns * 2 * Math.PI;
    pts.push(new THREE.Vector3(r * Math.cos(a), wire + l * t, r * Math.sin(a)));
  }
  return new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), N, wire, 8);
}
