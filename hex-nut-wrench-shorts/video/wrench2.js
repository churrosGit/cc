// Double box-end ratcheting wrench (reference-photo style): two ring heads joined by a flat bar
// with concave fillets, black 12-point ratchet gears, dome rivets, black reversing tabs, stamped sizes.
// Built in the same local XY / +Z-up convention as scene3d.js; head 1 (the one on the nut) is at the origin.
import * as THREE from 'three';

const extrude = (sh, depth, bevel = 0.05, seg = 3) => new THREE.ExtrudeGeometry(sh, {
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
