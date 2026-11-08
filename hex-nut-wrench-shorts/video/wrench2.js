// Double box-end ratcheting wrench (reference-photo style): two ring heads joined by a flat bar
// with concave fillets, black 12-point ratchet gears, dome rivets, black reversing tabs, stamped sizes.
// Built in the same local XY / +Z-up convention as scene3d.js; head 1 (the one on the nut) is at the origin.
import * as THREE from 'three';

function fixWinding(sh) {
  const outer = sh.getPoints(64); if (THREE.ShapeUtils.isClockWise(outer)) { const p = outer.slice().reverse(); const ns = new THREE.Shape(p); ns.holes = sh.holes; sh = ns; }
  sh.holes = sh.holes.map(h => { const hp = h.getPoints(64); return new THREE.Path(THREE.ShapeUtils.isClockWise(hp) ? hp : hp.slice().reverse()); });
  return sh;
}
const extrude = (sh, depth, bevel = 0.05, seg = 3) => new THREE.ExtrudeGeometry(fixWinding(sh), {
  depth, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments: seg, curveSegments: 64 });
const ring = (r, n = 128) => [...Array(n)].map((_, i) => new THREE.Vector2(r * Math.cos(i / n * 2 * Math.PI), r * Math.sin(i / n * 2 * Math.PI)));
// 12-point bore = union of two hexagons (circumradius rc) rotated 30°
function twelvePoint(rc) {
  const pts = [], inner = rc * Math.cos(Math.PI / 6) / Math.cos(Math.PI / 12);
  for (let k = 0; k < 12; k++) {
    const a = k * Math.PI / 6, b = a + Math.PI / 12;
    pts.push(new THREE.Vector2(rc * Math.cos(a), rc * Math.sin(a)), new THREE.Vector2(inner * Math.cos(b), inner * Math.sin(b)));
  }
  return pts;
}
// body outline: circle R1 at (0,0), circle R2 at (L,0), bar half-width w, tangent fillets rf
function bodyShape(R1, R2, L, w, rf) {
  const x1 = Math.sqrt((R1 + rf) ** 2 - (w + rf) ** 2), x2 = Math.sqrt((R2 + rf) ** 2 - (w + rf) ** 2);
  const s = new THREE.Shape();
  const a1 = Math.atan2(-(w + rf), -x1), a2 = Math.atan2(-(w + rf), x2);
  s.moveTo(x1 + rf * Math.cos(a1), w + rf + rf * Math.sin(a1));
  s.absarc(x1, w + rf, rf, a1, -Math.PI / 2, false);
  s.lineTo(L - x2, w);
  s.absarc(L - x2, w + rf, rf, -Math.PI / 2, a2, false);
  const t2 = Math.atan2(w + rf, -x2);
  s.absarc(L, 0, R2, t2, -t2, true);
  s.absarc(L - x2, -(w + rf), rf, -a2, Math.PI / 2, false);
  s.lineTo(x1, -w);
  s.absarc(x1, -(w + rf), rf, Math.PI / 2, -a1, false);
  const t1 = Math.atan2(-(w + rf), x1);
  s.absarc(0, 0, R1, t1, -t1, true);
  return s;
}
function stampTexture(text, w = 512, h = 128) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d');
  g.clearRect(0, 0, w, h); g.fillStyle = 'rgba(40,44,50,0.85)'; g.font = `800 ${h * 0.7}px Pretendard, sans-serif`;
  g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, w / 2, h / 2 + 4);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}

export function ratchetWrench(o = {}) {
  const R1 = o.R1 ?? 1.78, R2 = o.R2 ?? 2.02, L = o.L ?? 10.5, w = o.w ?? 0.82, rf = o.rf ?? 1.4;
  const bore1 = o.bore1 ?? 1.04, bore2 = o.bore2 ?? 1.26;           // 12-pt circumradius (nut = 1.0 fits head 1)
  const Tb = o.thick ?? 0.46, Th = Tb + 0.14;                       // bar and head thickness
  const chrome = o.chrome || new THREE.MeshStandardMaterial({ color: 0xc9ced6, metalness: 1, roughness: 0.27 });
  const black = o.black || new THREE.MeshStandardMaterial({ color: 0x16181c, metalness: 0.6, roughness: 0.42 });
  const g = new THREE.Group(), parts = {};
  const mesh = (geo, mat, z = 0) => { const m = new THREE.Mesh(geo, mat); m.position.z = z; m.castShadow = m.receiveShadow = true; g.add(m); return m; };
  // flat bar body (with the head bores cut through)
  const bs = bodyShape(R1, R2, L, w, rf);
  bs.holes.push(new THREE.Path(ring(R1 * 0.74).reverse()), new THREE.Path(ring(R2 * 0.74).map(v => v.add(new THREE.Vector2(L, 0))).reverse()));
  parts.body = mesh(extrude(bs, Tb - 0.1, 0.05), chrome, 0.07);
  // thicker head rings
  for (const [cx, R] of [[0, R1], [L, R2]]) {
    const hs = new THREE.Shape(ring(R - 0.02).map(v => v.add(new THREE.Vector2(cx, 0))));
    hs.holes.push(new THREE.Path(ring(R * 0.74).map(v => v.add(new THREE.Vector2(cx, 0))).reverse()));
    mesh(extrude(hs, Th - 0.12, 0.06), chrome, 0);
  }
  // black 12-point ratchet gears (the part that grips the nut); gear1 is exposed for animation
  const gearMesh = (cx, R, rc) => {
    const s = new THREE.Shape(ring(R * 0.74 - 0.01)); s.holes.push(new THREE.Path(twelvePoint(rc).reverse()));
    const m = new THREE.Mesh(extrude(s, Th - 0.2, 0.025, 2), black); m.position.set(cx, 0, 0.065); m.castShadow = m.receiveShadow = true; g.add(m); return m;
  };
  parts.gear1 = gearMesh(0, R1, bore1); parts.gear2 = gearMesh(L, R2, bore2);
  // dome rivets along the bar
  const rivGeo = new THREE.SphereGeometry(0.17, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2.4);
  for (const x of [R1 + 0.55, R1 + 2.45, L - R2 - 2.45, L - R2 - 0.55]) {
    const r = new THREE.Mesh(rivGeo, chrome); r.rotation.x = Math.PI / 2; r.position.set(x, 0, Tb + 0.02); r.castShadow = true; g.add(r);
    const rb = r.clone(); rb.rotation.x = -Math.PI / 2; rb.position.z = 0.0; g.add(rb);
  }
  // black reversing-lever tips peeking out at the head/neck junction
  const tabGeo = new THREE.CylinderGeometry(0.2, 0.2, Tb * 0.5, 24);
  for (const [cx, R, sgn] of [[0, R1, 1], [L, R2, -1]]) for (const side of [1, -1]) {
    const a = (sgn > 0 ? 0 : Math.PI) + sgn * side * 54 * Math.PI / 180;
    const t = new THREE.Mesh(tabGeo, black); t.rotation.x = Math.PI / 2;
    t.position.set(cx + (R - 0.02) * Math.cos(a), (R - 0.02) * Math.sin(a), Tb * 0.5); t.castShadow = true; g.add(t);
  }
  // stamped size marks
  const decal = (txt, x, size, rot) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(size * 2, size / 2), new THREE.MeshStandardMaterial({ map: stampTexture(txt), transparent: true, metalness: 0.6, roughness: 0.5, polygonOffset: true, polygonOffsetFactor: -2 }));
    m.position.set(x, 0, Tb + 0.03); m.rotation.z = rot; g.add(m);
  };
  decal('10', R1 + 1.5, 0.75, -Math.PI / 2); decal('13', L - R2 - 1.5, 0.75, -Math.PI / 2); decal('CR-V', L / 2, 1.0, 0);
  g.userData = { R1, R2, L, Th, parts };
  return g;
}

// ---------------------------------------------------------------------------------------------
// Same wrench, but head 1 is a working cut-away: removable cover plate over a cavity holding the
// black ratchet gear (outer saw teeth + 12-point bore), a pivoting pawl in a pocket toward the
// handle (+x), and a coil spring. Exposes the joints and kinematic constants like scene3d.ratchet().
import { P, gearPts, pawlPts } from './scene3d.js';
export function ratchetWrenchCut(o = {}) {
  const R1 = o.R1 ?? 2.45, R2 = o.R2 ?? 2.55, L = o.L ?? 11.8, w = o.w ?? 0.98, rf = o.rf ?? 1.5, H = o.H ?? 0.7;
  const n = o.n ?? 20, rt = o.rt ?? 1.7, rr = rt - (o.depth ?? 0.32), m = 2, s = 360 / n, rot = 0.37 * s;
  const rOut = rt + 0.12, rSpring = rt + 0.56, rPocket = rSpring + 0.05;
  const chrome = o.chrome || new THREE.MeshStandardMaterial({ color: 0xc9ced6, metalness: 1, roughness: 0.27 });
  const coverM = o.coverM || chrome;
  const black = o.black || new THREE.MeshStandardMaterial({ color: 0x16181c, metalness: 0.6, roughness: 0.42 });
  const pawlM = o.pawlM || new THREE.MeshStandardMaterial({ color: 0xff7a1a, metalness: 0.55, roughness: 0.3 });
  const springM = o.springM || new THREE.MeshStandardMaterial({ color: 0x7fb6ff, metalness: 0.9, roughness: 0.25 });
  const pinM = o.pinM || new THREE.MeshStandardMaterial({ color: 0x8a8f98, metalness: 1, roughness: 0.3 });
  const g = new THREE.Group(), parts = {};
  const add = (k, m) => { m.castShadow = m.receiveShadow = true; g.add(m); if (k) parts[k] = m; return m; };
  const K = Math.round((0 + m * s / 2 - rot) / s), aEnd = rot + K * s;           // pawl centred on +x
  const pw = pawlPts(rr + 0.018, rt + 0.018, s, rot, aEnd, m, rOut);
  { const e = 0.35 * Math.PI / 180, c = Math.cos(e), sn = Math.sin(e);     // hairline gap at the contact face
    pw.pts = pw.pts.map(q => new THREE.Vector2(q.x * c - q.y * sn, q.x * sn + q.y * c)); }
  const a1 = pw.A0 - s * 0.7, a2 = aEnd + s * 0.9;
  const cavity = () => { const pts = [];
    for (let i = 0; i <= 140; i++) pts.push(P(rt + 0.02, a2 + (360 - (a2 - a1)) * i / 140));
    for (let i = 0; i <= 30; i++) pts.push(P(rPocket, a1 + (a2 - a1) * i / 30));
    return pts; };
  // body with the cavity at head 1 and a plain bore at head 2
  const bs = bodyShape(R1, R2, L, w, rf);
  bs.holes.push(new THREE.Path(cavity()), new THREE.Path(ring(R2 * 0.74).map(v => v.add(new THREE.Vector2(L, 0))).reverse()));
  const body = add('body', new THREE.Mesh(extrude(bs, H - 0.1, 0.05), chrome)); body.position.z = 0.05;
  // floor and removable cover share the cavity outline
  const plate = (inner) => { const sh = new THREE.Shape(cavity()); sh.holes.push(new THREE.Path(ring(inner).reverse())); return extrude(sh, 0.1, 0); };
  add('floor', new THREE.Mesh(plate(1.2), chrome));
  const cover = add('cover', new THREE.Mesh(plate(1.55), coverM)); cover.position.z = H - 0.1;
  // black gear: outer ratchet teeth + 12-point bore
  const gs = new THREE.Shape(gearPts(rr, rt, n, rot)); gs.holes.push(new THREE.Path(twelvePoint(o.bore1 ?? 1.04).reverse()));
  const gear = add('gear', new THREE.Mesh(extrude(gs, H - 0.24, 0.01, 1), black)); gear.position.z = 0.11;
  // head 2: closed black 12-point insert
  const g2 = new THREE.Shape(ring(R2 * 0.74 - 0.01)); g2.holes.push(new THREE.Path(twelvePoint(o.bore2 ?? 1.3).reverse()));
  const gm2 = add('gear2', new THREE.Mesh(extrude(g2, H - 0.16, 0.025, 2), black)); gm2.position.set(L, 0, 0.07);
  // sliding pawl: slides radially (along its mid-angle) in the pocket, pushed back by the spring
  const midA = (pw.A0 + aEnd) / 2, dir = P(1, midA);
  const pg = new THREE.Group(); g.add(pg); parts.pawlPivot = pg;
  const pm = new THREE.Mesh(extrude(new THREE.Shape(pw.pts), H - 0.24, 0.01, 1), pawlM); pm.castShadow = pm.receiveShadow = true;
  pm.position.z = 0.11; pg.add(pm); parts.pawl = pm;
  // spring
  const sA = aEnd - m * s * 0.3, p1 = P(rSpring, sA), p2 = P(rOut, sA), Ls = p1.distanceTo(p2), zc = 0.11 + (H - 0.24) / 2, cp = [];
  for (let i = 0; i <= 150; i++) { const t = i / 150, an = t * 5 * 2 * Math.PI; cp.push(new THREE.Vector3(t * Ls, 0.08 * Math.cos(an), zc + 0.08 * Math.sin(an))); }
  const sg = new THREE.Group(); sg.position.set(p1.x, p1.y, 0); sg.rotation.z = Math.atan2(p2.y - p1.y, p2.x - p1.x); g.add(sg); parts.springGroup = sg;
  const spm = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(cp), 200, 0.02, 8), springM); spm.castShadow = true; sg.add(spm); parts.spring = spm;
  // rivets, reversing-lever tips, stamps
  const rivGeo = new THREE.SphereGeometry(0.18, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2.4);
  for (const x of [R1 + 0.6, R1 + 2.6, L - R2 - 2.6, L - R2 - 0.6]) for (const up of [1, -1]) {
    const r = new THREE.Mesh(rivGeo, chrome); r.rotation.x = up * Math.PI / 2; r.position.set(x, 0, up > 0 ? H : 0); r.castShadow = true; g.add(r); }
  const tabGeo = new THREE.CylinderGeometry(0.21, 0.21, H * 0.5, 24);
  for (const [cx, R, sgn] of [[0, R1, 1], [L, R2, -1]]) for (const side of [1, -1]) {
    const a = (sgn > 0 ? 0 : Math.PI) + sgn * side * 52 * Math.PI / 180, t = new THREE.Mesh(tabGeo, black);
    t.rotation.x = Math.PI / 2; t.position.set(cx + (R - 0.02) * Math.cos(a), (R - 0.02) * Math.sin(a), H / 2); t.castShadow = true; g.add(t); }
  const decal = (txt, x, size, rotz) => { const mm = new THREE.Mesh(new THREE.PlaneGeometry(size * 2, size / 2), new THREE.MeshStandardMaterial({ map: stampTexture(txt), transparent: true, metalness: 0.6, roughness: 0.5, polygonOffset: true, polygonOffsetFactor: -2 }));
    mm.position.set(x, 0, H + 0.006); mm.rotation.z = rotz; g.add(mm); };
  decal('10', R1 + 1.6, 0.8, -Math.PI / 2); decal('13', L - R2 - 1.6, 0.8, -Math.PI / 2); decal('CR-V', L / 2, 1.05, 0);
  // collision-based pawl angle: smallest rotation about the pivot that keeps pawl and gear apart
  const sawRm = (a) => { const u = ((((a - rot) % s) + s) % s) / s; return rt - (rt - rr) * u; };
  const insideGear = (x, y) => { const r = Math.hypot(x, y); if (r > rt + 1e-4) return false; const a = -Math.atan2(y, x) * 180 / Math.PI; return r < sawRm(a) - 1e-4; };
  const tips = [...Array(n)].map((_, k) => P(rt, rot + k * s));
  const inPoly = (x, y, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const a = poly[i], b = poly[j]; if (((a.y > y) !== (b.y > y)) && (x < (b.x - a.x) * (y - a.y) / (b.y - a.y) + a.x)) c = !c; } return c; };
  const pawlPoly = pw.pts;
  function collides(d, relDeg) {               // relDeg = gear rotation relative to the body (math degrees, ccw +)
    const gr = -relDeg * Math.PI / 180, cg = Math.cos(gr), sg = Math.sin(gr);
    const poly = pawlPoly.map(q => new THREE.Vector2(q.x + dir.x * d, q.y + dir.y * d));
    for (const q of poly) { const gx = q.x * cg - q.y * sg, gy = q.x * sg + q.y * cg; if (insideGear(gx, gy)) return true; }
    const cb = Math.cos(-gr), sb = Math.sin(-gr), c0 = P(rt, midA);
    for (const t of tips) { const bx = t.x * cb - t.y * sb, by = t.x * sb + t.y * cb; if (Math.hypot(bx - c0.x, by - c0.y) < 1.0 && inPoly(bx, by, poly)) return true; }
    return false;
  }
  function pawlLift(relDeg) {
    if (!collides(0, relDeg)) return 0;
    let d = 0; while (d < 0.6 && collides(d, relDeg)) d += 0.004;
    let lo = Math.max(0, d - 0.004), hi = d; for (let i = 0; i < 8; i++) { const mid = (lo + hi) / 2; if (collides(mid, relDeg)) lo = mid; else hi = mid; }
    return hi + 0.004;
  }
  const setPawl = (d) => { pg.position.set(dir.x * d, dir.y * d, 0);
    const q = new THREE.Vector2(p2.x + dir.x * d, p2.y + dir.y * d); sg.scale.x = q.distanceTo(p1) / Ls; };
  const zt = H - 0.13;
  g.userData = { pawlLift, setPawl, R1, R2, L, H, s, depth: rt - rr, springLen: Ls, parts,
    anchors: { pawl: new THREE.Vector3(...P((rt + rOut) / 2, (pw.A0 + aEnd) / 2).toArray(), zt),
      spring: new THREE.Vector3(...P((rOut + rSpring) / 2, sA).toArray(), zc + 0.1),
      gear: a => new THREE.Vector3(...P(rt - 0.06, a).toArray(), zt), bore: new THREE.Vector3(...P(1.3, 200).toArray(), zt) } };
  return g;
}
