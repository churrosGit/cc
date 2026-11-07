// Shared 3D models for the wrench shorts (three.js). Units: nut circumradius = 1.
// Tool shapes are drawn in a local XY plane and extruded along +Z; place them inside
// toolFrame(), which lays that plane flat (Z -> world up). Angles use a mirrored
// convention so that +angle = clockwise seen from above (= tightening direction).
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const D = Math.PI / 180;
export const P = (r, a, cx = 0, cy = 0) => new THREE.Vector2(cx + r * Math.cos(a * D), cy - r * Math.sin(a * D));
const shape = pts => new THREE.Shape(pts);
const path = pts => new THREE.Path(pts);

export function toolFrame() {            // XY plane -> horizontal, +Z -> +Y (up)
  const g = new THREE.Group(); g.rotation.x = -Math.PI / 2; return g;
}

export function setupRenderer(canvas, { alpha = true, exposure = 1 } = {}) {
  const r = new THREE.WebGLRenderer({ canvas, antialias: true, alpha, preserveDrawingBuffer: true });
  r.setPixelRatio(1); r.setSize(canvas.width, canvas.height, false);
  r.outputColorSpace = THREE.SRGBColorSpace;
  r.toneMapping = THREE.ACESFilmicToneMapping; r.toneMappingExposure = exposure;
  r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
  return r;
}
export function envMap(renderer, scene, intensity = 1) {
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = intensity;
}

const hexPts = (r, rot = 0) => [...Array(6)].map((_, i) => P(r, rot + i * 60));
const circlePts = (r, n = 96, cx = 0, cy = 0) => [...Array(n)].map((_, i) => P(r, i * 360 / n, cx, cy));
const extrude = (sh, depth, bevel = 0.03, seg = 2) => new THREE.ExtrudeGeometry(sh, {
  depth, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments: seg, curveSegments: 48 });

// ---------- nut & bolt ----------
export function nut(mat, { r = 1, h = 0.8, rot = 0 } = {}) {
  const sh = shape(hexPts(r - 0.05, rot)); sh.holes.push(path(circlePts(0.5, 64).reverse()));
  const m = new THREE.Mesh(extrude(sh, h - 0.1, 0.05, 3), mat); m.position.z = 0.05;
  m.castShadow = m.receiveShadow = true; return m;
}
export function bolt(mat, { len = 2.6, z0 = -1.2 } = {}) {
  const g = new THREE.Group();
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.47, 0.47, len, 48), mat);
  shaft.rotation.x = Math.PI / 2; shaft.position.z = z0 + len / 2; g.add(shaft);
  // helical thread
  const turns = len / 0.16, pts = [];
  for (let i = 0; i <= turns * 40; i++) { const t = i / 40; pts.push(new THREE.Vector3(0.47 * Math.cos(t * 2 * Math.PI), 0.47 * Math.sin(t * 2 * Math.PI), z0 + 0.05 + t * 0.16)); }
  const th = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), pts.length, 0.045, 6), mat);
  g.add(th);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.47, 0.08, 48), mat);
  cap.rotation.x = Math.PI / 2; cap.position.z = z0 + len + 0.04; g.add(cap);
  g.traverse(o => { if (o.isMesh) o.castShadow = o.receiveShadow = true; });
  return g;
}

// ---------- open-end spanner (jaw toward +x, handle 15° off-axis) ----------
export function spanner(mat, { r = 1, t = 0.42, len = 9 } = {}) {
  const f = r * Math.sqrt(3) / 2 * 1.035, R = 1.82 * r, cx = -0.18 * r;
  const th0 = Math.asin(f / R), xTop = cx + Math.sqrt(R * R - f * f);
  const s = new THREE.Shape();
  s.moveTo(xTop, f); s.lineTo(-0.5 * r, f);
  s.absarc(-0.5 * r, 0, f, Math.PI / 2, 3 * Math.PI / 2, false);
  s.lineTo(xTop, -f); s.absarc(cx, 0, R, -th0, th0 - 2 * Math.PI, true);
  const g = new THREE.Group();
  const head = new THREE.Mesh(extrude(s, t, 0.05, 3), mat); g.add(head);
  // handle (direction 195° in mirrored convention = -165° math)
  const hs = new THREE.Shape();
  hs.moveTo(1.0 * r, -0.8 * r); hs.lineTo(len * r, -0.6 * r);
  hs.absarc(len * r, 0, 0.6 * r, -Math.PI / 2, Math.PI / 2, false);
  hs.lineTo(1.0 * r, 0.8 * r); hs.closePath();
  const hm = new THREE.Mesh(extrude(hs, t * 0.82, 0.05, 3), mat);
  hm.position.z = t * 0.09; hm.rotation.z = -195 * D; g.add(hm);
  g.traverse(o => { if (o.isMesh) o.castShadow = o.receiveShadow = true; });
  g.position.z = 0.19;                 // sit at nut mid-height
  return g;
}

// ---------- ratcheting ring head with cut-away internals ----------
function sawR(a, rot, s, rr, rt) { const u = ((((a - rot) % s) + s) % s) / s; return rt - (rt - rr) * u; }
function gearPts(rr, rt, n, rot, sub = 4) {
  const s = 360 / n, pts = [];
  for (let i = 0; i < n; i++) { const a = rot + i * s; pts.push(P(rr, a)); for (let j = 0; j < sub; j++) pts.push(P(rt - (rt - rr) * j / sub, a + s * j / sub)); }
  return pts;
}
function pawlPts(rr, rt, s, rot, aEnd, m, rOut) {
  const A0 = aEnd - m * s + s * 0.45, pts = []; let a = A0;
  pts.push(P(sawR(a, rot, s, rr, rt), a));
  for (let k = Math.ceil((A0 - rot) / s + 1e-6); ; k++) {
    const af = rot + k * s; if (af > aEnd + 1e-6) break;
    for (let t = 1; t < 5; t++) { const aa = a + (af - a) * t / 5; pts.push(P(sawR(aa, rot, s, rr, rt), aa)); }
    pts.push(P(rr, af)); if (af < aEnd - 1e-6) pts.push(P(rt, af)); a = af;
  }
  pts.push(P(rOut, aEnd));
  for (let t = 1; t <= 20; t++) { const aa = aEnd - (aEnd - A0) * t / 20; pts.push(P(rOut, aa)); }
  return { pts, A0 };
}

export function ratchet(M, o = {}) {
  const rt = o.rt || 1.62, n = o.n || 72, T = o.T ?? 180, m = o.pawlTeeth || 4;
  const rr = rt - (o.toothDepth || 0.1), s = 360 / n, rot = o.rot ?? 0.37 * s;
  const K = Math.round((T + m * s / 2 - rot) / s), aEnd = rot + K * s;
  const rOut = rt + 0.2, rSpring = rt + 0.5, RH = rt + 0.78, H = o.H || 0.7, floor = 0.12, gh = 0.46;
  const g = new THREE.Group(), parts = {};
  const add = (k, mesh) => { mesh.castShadow = mesh.receiveShadow = true; g.add(mesh); parts[k] = mesh; return mesh; };
  // housing wall with gear bore + pawl pocket
  const pw = pawlPts(rr, rt, s, rot, aEnd, m, rOut);
  const a1 = pw.A0 - s * 1.6, a2 = aEnd + s * 1.4, hole = [];
  for (let i = 0; i <= 140; i++) hole.push(P(rt + 0.02, a2 + (360 - (a2 - a1)) * i / 140));
  for (let i = 0; i <= 30; i++) hole.push(P(rSpring + 0.06, a1 + (a2 - a1) * i / 30));
  const hs = shape(circlePts(RH, 160)); hs.holes.push(path(hole.reverse()));
  add('housing', new THREE.Mesh(extrude(hs, H, 0.04, 3), M.housing));
  const fs = shape(circlePts(RH - 0.02, 160)); fs.holes.push(path(circlePts(rr - 0.12, 120).reverse()));
  add('floor', new THREE.Mesh(extrude(fs, floor, 0), M.housing));
  // handle with concave root following the head
  const L = o.handleLen || 7, w0 = 0.95, w1 = 0.7, phi = Math.asin(w0 / (RH - 0.25));
  const hd = new THREE.Shape(); const r0 = RH - 0.25;
  hd.moveTo(r0 * Math.cos(phi), -w0);
  hd.lineTo(L, -w1); hd.absarc(L, 0, w1, -Math.PI / 2, Math.PI / 2, false); hd.lineTo(r0 * Math.cos(phi), w0);
  hd.absarc(0, 0, r0, phi, -phi, true);
  const hm = add('handle', new THREE.Mesh(extrude(hd, H * 0.8, 0.05, 3), M.housing));
  hm.position.z = H * 0.1; hm.rotation.z = -T * D;
  // gear with hex bore
  const gs = shape(gearPts(rr, rt, n, rot)); gs.holes.push(path(hexPts(1.03).reverse()));
  const gm = add('gear', new THREE.Mesh(extrude(gs, gh - 0.02, 0.01, 1), M.gear)); gm.position.z = floor + 0.01;
  // pawl on a pivot group (rotate pawlPivot.rotation.z to lift it) + pivot pin
  const pivotA = pw.A0 + s * 0.3, pv = P(rOut - 0.14, pivotA);
  const pg = new THREE.Group(); pg.position.set(pv.x, pv.y, 0); g.add(pg); parts.pawlPivot = pg;
  const pm = new THREE.Mesh(extrude(shape(pw.pts), gh - 0.02, 0.01, 1), M.pawl);
  pm.castShadow = pm.receiveShadow = true; pm.position.set(-pv.x, -pv.y, floor + 0.01); pg.add(pm); parts.pawl = pm;
  const pin = add('pin', new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, H, 24), M.pin));
  pin.rotation.x = Math.PI / 2; pin.position.set(pv.x, pv.y, H / 2);
  // coil spring pressing the pawl inward; built along local +x so springGroup.scale.x compresses it
  const sA = aEnd - m * s * 0.3, p1 = P(rSpring + 0.04, sA), p2 = P(rOut, sA);
  const Ls = p1.distanceTo(p2), zc = floor + gh / 2, cp = [];
  for (let i = 0; i <= 6 * 30; i++) { const t = i / (6 * 30), ang = t * 6 * 2 * Math.PI;
    cp.push(new THREE.Vector3(t * Ls, 0.09 * Math.cos(ang), zc + 0.09 * Math.sin(ang))); }
  const sg = new THREE.Group(); sg.position.set(p1.x, p1.y, 0); sg.rotation.z = Math.atan2(p2.y - p1.y, p2.x - p1.x); g.add(sg); parts.springGroup = sg;
  const spm = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(cp), 240, 0.022, 8), M.spring);
  spm.castShadow = spm.receiveShadow = true; sg.add(spm); parts.spring = spm;
  // which pawl rotation sign lifts the teeth outward, and the lever arms
  const tooth = P(rt - (rt - rr) / 2, aEnd - s * 0.5), arm = tooth.distanceTo(pv);
  const rotAbout = (q, a) => { const c = Math.cos(a), sn = Math.sin(a), dx = q.x - pv.x, dy = q.y - pv.y; return new THREE.Vector2(pv.x + dx * c - dy * sn, pv.y + dx * sn + dy * c); };
  const pawlSign = rotAbout(tooth, 0.01).length() > tooth.length() ? 1 : -1;
  const springArm = p2.distanceTo(pv);
  // optional top cover (for x-ray look)
  if (M.cover) { const cs = shape(circlePts(RH, 160)); cs.holes.push(path(circlePts(1.15, 96).reverse()));
    const c = add('cover', new THREE.Mesh(extrude(cs, 0.1, 0.02), M.cover)); c.position.z = H + 0.02; c.castShadow = false; }
  g.position.z = -0.0;
  const z = floor + gh;
  g.userData = { rt, rr, RH, H, aEnd, A0: pw.A0, T, parts, s, depth: rt - rr, pawlSign, arm, springArm, springLen: Ls,
    anchors: { pawl: new THREE.Vector3(...P((rt + rOut) / 2, (pw.A0 + aEnd) / 2).toArray(), z),
      spring: new THREE.Vector3(...P((rOut + rSpring) / 2, sA).toArray(), zc + 0.1),
      gear: (a) => new THREE.Vector3(...P(rt - 0.05, a).toArray(), z), pin: new THREE.Vector3(pv.x, pv.y, H) } };
  return g;
}

// curved arrow around the bolt axis, in tool-frame coords (+angle = clockwise from above)
export function arcArrow(mat, { r = 3, a1 = 0, a2 = 60, z = 0.5, tube = 0.06, head = 0.22 } = {}) {
  const pts = [], N = 64, dir = Math.sign(a2 - a1), aStop = a2 - dir * (head * 1.1 / r) / D;
  for (let i = 0; i <= N; i++) { const v = P(r, a1 + (aStop - a1) * i / N); pts.push(new THREE.Vector3(v.x, v.y, z)); }
  const g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), N, tube, 12), mat));
  const tip = P(r, a2), base = P(r, aStop);
  const cone = new THREE.Mesh(new THREE.ConeGeometry(head * 0.55, head * 1.2, 24), mat);
  const mid = new THREE.Vector3((tip.x + base.x) / 2, (tip.y + base.y) / 2, z);
  cone.position.copy(mid);
  cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(tip.x - base.x, tip.y - base.y, 0).normalize());
  g.add(cone); return g;
}

export function ghostify(obj, mat) {
  const c = obj.clone(true);
  c.traverse(o => { if (o.isMesh) { o.material = mat; o.castShadow = false; } });
  return c;
}

// project a world-space point to CSS pixels on the canvas
export function toScreen(v, camera, w, h, viewport = [0, 0, w, h]) {
  const p = v.clone().project(camera);
  return [viewport[0] + (p.x + 1) / 2 * viewport[2], viewport[1] + (1 - p.y) / 2 * viewport[3]];
}
export function worldOf(obj, local) { obj.updateWorldMatrix(true, false); return local.clone().applyMatrix4(obj.matrixWorld); }
