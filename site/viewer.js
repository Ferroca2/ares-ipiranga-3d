/* ---------- viewer 3D ---------- */
const box = document.getElementById("viewer"), status = document.getElementById("status");
let hemi, sun, fill;
// luz pré-calculada no Cycles chega como occlusionTexture (aoMap): ela passa a ser a única fonte, sobre uma luz ambiente branca
const BAKED = { ambient: 1.25, exposure: 1.0 };
function bakedLighting(on) {
  hemi.color.set(on ? 0xffffff : 0xfffaf2); hemi.groundColor.set(on ? 0xffffff : 0x6f675e);
  hemi.intensity = on ? BAKED.ambient : 0.62; sun.visible = fill.visible = !on;
  renderer.toneMappingExposure = on ? BAKED.exposure : 1.0;
}
let renderer, scene, camera, controls, model, showCeiling = false, walking = false, fly = null;
const keys = new Set(), clock = new THREE.Clock(), walkhint = document.getElementById("walkhint");
// olho a 1,55 m; coordenadas do modelo: x, altura, y da planta
const ROOMS = {
  sala:     [[3.75, 1.55, 6.60], [0.40, 1.20, 5.95]],
  cozinha:  [[0.70, 1.55, 5.85], [3.70, 1.20, 7.25]],
  corredor: [[2.52, 1.55, 5.45], [2.52, 1.30, 2.60]],
  dorm1:    [[2.25, 1.55, 2.30], [0.55, 0.90, 0.30]],
  dorm2:    [[1.85, 1.55, 4.35], [0.25, 1.00, 3.05]],
  banho:    [[3.10, 1.55, 4.85], [3.95, 1.10, 3.30]],
};
// setas no piso estilo street view: [destino, posição da seta (x, y da planta), passagem pela porta]
const NAV = {
  sala:     [["cozinha", [1.90, 6.40]], ["corredor", [2.55, 5.55], [[2.55, 5.90]]]],
  cozinha:  [["sala", [2.60, 6.50]], ["corredor", [2.50, 5.50], [[2.50, 5.90]]]],
  corredor: [["dorm1", [2.55, 3.70], [[2.52, 3.40]]], ["dorm2", [2.25, 4.15], [[1.98, 4.15]]],
             ["banho", [2.72, 4.50], [[2.70, 4.66], [3.05, 4.66]]], ["sala", [3.05, 6.15], [[2.55, 5.90]]],
             ["cozinha", [2.00, 6.15], [[2.50, 5.90]]]],
  dorm1:    [["corredor", [2.52, 3.25], [[2.52, 3.62]]]],
  dorm2:    [["corredor", [2.32, 4.08], [[2.09, 4.08]]]],
  banho:    [["corredor", [2.62, 4.66], [[2.95, 4.66]]]],
};
const ROOM_LABEL = { sala: "Sala", cozinha: "Cozinha", corredor: "Corredor", dorm1: "Dormitório 1", dorm2: "Dormitório 2", banho: "Banho" };
let room = null, arrows = null;
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
const cache = {};

const CENTER = new THREE.Vector3(2.1, 0.8, 3.8);
function initViewer() {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  box.prepend(renderer.domElement);
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(38, 16 / 9, 0.05, 200);
  hemi = new THREE.HemisphereLight(0xfffaf2, 0x6f675e, 0.62); scene.add(hemi);
  sun = new THREE.DirectionalLight(0xfff1e0, 0.85); sun.position.set(-6, 10, 4); scene.add(sun);
  fill = new THREE.DirectionalLight(0xdfe8ff, 0.28); fill.position.set(8, 6, 10); scene.add(fill);
  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.maxPolarAngle = Math.PI * 0.49;
  controls.minDistance = 1.5; controls.maxDistance = 25;
  camera.position.set(8.5, 9, 12.5); controls.target.copy(CENTER); controls.update();
  new ResizeObserver(resize).observe(box); resize();
  box.tabIndex = 0;
  let down = null;
  const hit = e => {
    if (!arrows) return null;
    const r = renderer.domElement.getBoundingClientRect();
    ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const h = ray.intersectObjects(arrows.children, true)[0];
    if (!h) return null;
    let o = h.object; while (o && !o.userData.to) o = o.parent;
    return o;
  };
  renderer.domElement.addEventListener("pointerdown", e => { down = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener("pointerup", e => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 6) return;
    const o = hit(e); if (o) goVia(o.userData.to, o.userData.via);
  });
  renderer.domElement.addEventListener("pointermove", e => { renderer.domElement.style.cursor = hit(e) ? "pointer" : ""; });
  addEventListener("keydown", e => {
    if (!walking || !(box.matches(":hover") || document.activeElement === box)) return;
    const k = e.key.toLowerCase();
    if (["w", "a", "s", "d", "arrowup", "arrowdown", "arrowleft", "arrowright"].includes(k)) { keys.add(k); e.preventDefault(); }
  });
  addEventListener("keyup", e => keys.delete(e.key.toLowerCase()));
  addEventListener("blur", () => keys.clear());
  (function loop() {
    requestAnimationFrame(loop);
    const dt = Math.min(clock.getDelta(), 0.1);
    if (fly) {
      fly.t = Math.min(1, fly.t + dt / fly.dur);
      fly.at(fly.t < 0.5 ? 2 * fly.t * fly.t : 1 - Math.pow(-2 * fly.t + 2, 2) / 2);
      if (fly.t === 1) { fly = null; if (walking) showArrows(); }
    } else if (walking && keys.size) walk(dt);
    controls.update(); renderer.render(scene, camera);
  })();
}
function resize() {
  const w = box.clientWidth, h = box.clientHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
}
function flyTo(pos, target) {
  const p0 = camera.position.clone(), t0 = controls.target.clone();
  fly = { t: 0, dur: 1.1, at: k => { camera.position.lerpVectors(p0, pos, k); controls.target.lerpVectors(t0, target, k); } };
}
// percorre a poligonal (passando pelas portas) virando a cabeça aos poucos para a direção final
function flyPath(pts, dirEnd) {
  const d0 = controls.target.clone().sub(camera.position).normalize();
  const seg = pts.slice(1).map((q, i) => q.distanceTo(pts[i])), len = seg.reduce((a, b) => a + b, 0) || 1;
  fly = { t: 0, dur: Math.min(2.6, Math.max(0.9, len / 1.5)), at: k => {
    let d = k * len, i = 0;
    while (i < seg.length - 1 && d > seg[i]) d -= seg[i++];
    const p = pts[i].clone().lerp(pts[i + 1], seg[i] ? Math.min(1, d / seg[i]) : 1);
    camera.position.copy(p);
    controls.target.copy(p).addScaledVector(d0.clone().lerp(dirEnd, k).normalize(), 0.01);
  } };
}
function label(text) {
  const c = document.createElement("canvas"), g = c.getContext("2d");
  c.width = 512; c.height = 128;
  g.font = "600 52px 'Instrument Sans', Arial, sans-serif";
  const w = Math.min(500, g.measureText(text).width + 64);
  g.fillStyle = "rgba(20,21,23,.78)"; g.beginPath(); g.roundRect((512 - w) / 2, 22, w, 84, 42); g.fill();
  g.fillStyle = "#fff"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(text, 256, 66);
  const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, transparent: true }));
  sp.scale.set(0.62, 0.155, 1); sp.renderOrder = 11;
  return sp;
}
function arrowMesh() {
  const g = new THREE.Group();
  const disc = new THREE.Mesh(new THREE.CircleGeometry(0.2, 40), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.9, depthTest: false, depthWrite: false, toneMapped: false, side: THREE.DoubleSide }));
  const sh = new THREE.Shape();
  sh.moveTo(0, 0.12); sh.lineTo(0.11, -0.02); sh.lineTo(0.06, -0.02); sh.lineTo(0, 0.05); sh.lineTo(-0.06, -0.02); sh.lineTo(-0.11, -0.02); sh.closePath();
  const chev = new THREE.Mesh(new THREE.ShapeGeometry(sh), new THREE.MeshBasicMaterial({ color: 0x1f4fd1, transparent: true, depthTest: false, depthWrite: false, toneMapped: false, side: THREE.DoubleSide }));
  chev.position.z = 0.001; disc.renderOrder = 10; chev.renderOrder = 11;
  const flat = new THREE.Group(); flat.add(disc, chev); flat.rotation.x = -Math.PI / 2;
  g.add(flat);
  return g;
}
function showArrows() {
  hideArrows();
  if (!NAV[room]) return;
  arrows = new THREE.Group();
  const eye = camera.position;
  NAV[room].forEach(([to, at, via]) => {
    const a = arrowMesh(), pos = new THREE.Vector3(at[0], 0.03, at[1]);
    a.position.copy(pos);
    // a ponta aponta da posição atual para a seta e segue até a porta
    const aim = via ? new THREE.Vector3(via[0][0], 0, via[0][1]) : new THREE.Vector3(ROOMS[to][0][0], 0, ROOMS[to][0][2]);
    const dir = aim.sub(new THREE.Vector3(pos.x, 0, pos.z));
    if (dir.lengthSq() < 1e-4) dir.set(pos.x - eye.x, 0, pos.z - eye.z);
    a.rotation.y = Math.atan2(-dir.x, -dir.z);
    const tag = label(ROOM_LABEL[to]); tag.position.set(at[0], 0.36, at[1]);
    a.userData = tag.userData = { to, via };
    arrows.add(a, tag);
  });
  scene.add(arrows);
  showChips();
}
function hideArrows() { if (arrows) { scene.remove(arrows); arrows = null; } navchips.hidden = true; }
// os mesmos destinos em botões fixos, para quando a seta ficar fora do quadro
const navchips = document.getElementById("navchips");
navchips.addEventListener("click", e => { const b = e.target.closest("[data-to]"); if (b) { const n = NAV[room].find(x => x[0] === b.dataset.to); goVia(n[0], n[2]); } });
function showChips() {
  navchips.innerHTML = `<span class="label">ir para</span>` + NAV[room].map(([to]) => `<button type="button" data-to="${to}">${ROOM_LABEL[to]} →</button>`).join("");
  navchips.hidden = false;
}
function goVia(to, via) {
  const [eye, look] = ROOMS[to].map(v => new THREE.Vector3(...v));
  const pts = [camera.position.clone(), ...(via || []).map(([x, y]) => new THREE.Vector3(x, 1.55, y)), eye];
  let dir = lookDir(eye, look);
  if (to === "corredor" && via) dir = lookDir(pts[pts.length - 2], eye);
  setRoom(to); hideArrows(); flyPath(pts, dir);
}
// olhar levemente para baixo (cerca de 27°) para as setas do piso entrarem no quadro
function lookDir(from, to) {
  const d = to.clone().sub(from).setY(0).normalize(); d.y = -0.5; return d.normalize();
}
function setRoom(name) {
  room = name;
  document.querySelectorAll("[data-room]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.room === name)));
}
function exitRoom() {
  if (!walking) return;
  walking = false; keys.clear(); walkhint.hidden = true; scene.background = null; room = null; hideArrows();
  camera.fov = 38; camera.updateProjectionMatrix();
  Object.assign(controls, { enableZoom: true, enablePan: true, rotateSpeed: 1, minDistance: 1.5, maxDistance: 25, minPolarAngle: 0, maxPolarAngle: Math.PI * 0.49 });
  document.querySelectorAll("[data-room]").forEach(b => b.setAttribute("aria-pressed", "false"));
  applyCeiling();
}
function home() { exitRoom(); flyTo(new THREE.Vector3(8.5, 9, 12.5), CENTER.clone()); }
function enterRoom(name) {
  const [eye, look] = ROOMS[name].map(v => new THREE.Vector3(...v));
  walking = true; walkhint.hidden = false; scene.background = new THREE.Color(0xdde7ee);
  camera.fov = 68; camera.updateProjectionMatrix();
  // alvo a 1 cm do olho: girar a órbita equivale a virar a cabeça
  Object.assign(controls, { enableZoom: false, enablePan: false, rotateSpeed: -0.35, minDistance: 0, maxDistance: 1, minPolarAngle: 0.2, maxPolarAngle: Math.PI - 0.2 });
  setRoom(name); hideArrows();
  applyCeiling();
  flyTo(eye, eye.clone().addScaledVector(lookDir(eye, look), 0.01));
  box.focus({ preventScroll: true });
}
function walk(dt) {
  const fwd = controls.target.clone().sub(camera.position).setY(0).normalize();
  const right = new THREE.Vector3(-fwd.z, 0, fwd.x), move = new THREE.Vector3();
  if (keys.has("w") || keys.has("arrowup")) move.add(fwd);
  if (keys.has("s") || keys.has("arrowdown")) move.sub(fwd);
  if (keys.has("d") || keys.has("arrowright")) move.add(right);
  if (keys.has("a") || keys.has("arrowleft")) move.sub(right);
  if (!move.lengthSq()) return;
  move.normalize().multiplyScalar(1.4 * dt);
  const p = camera.position.clone().add(move);
  p.x = THREE.MathUtils.clamp(p.x, 0.15, 4.1); p.z = THREE.MathUtils.clamp(p.z, 0.15, 7.45);
  move.subVectors(p, camera.position);
  camera.position.add(move); controls.target.add(move);
}
function applyCeiling() {
  if (!model) return;
  model.traverse(o => { if (/^(Teto|Sanca)/.test(o.name)) o.visible = showCeiling || walking; });
}
function fetchGLTF(url) {
  if (cache[url]) return cache[url];
  // o frame bloqueia URLs data:, então o buffer embutido vira um GLB montado em memória
  return cache[url] = fetch(url).then(r => r.json()).then(json => new Promise((ok, bad) => {
    const b64 = json.buffers[0].uri.split(",")[1];
    const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    delete json.buffers[0].uri;
    new THREE.GLTFLoader().parse(toGLB(json, bin), "", g => {
      g.scene.traverse(o => [].concat(o.material || []).forEach(m => {
        if (m.aoMap) { m.aoMapIntensity = 1; g.baked = true; }
        if (/^Vidro/.test(m.name)) Object.assign(m, { transparent: true, opacity: m.name === "Vidro" ? 0.12 : 0.45, metalness: 0, roughness: 0.05, depthWrite: false });
      }));
      ok(g);
    }, bad);
  })).catch(e => { delete cache[url]; throw e; });
}
const fail = err => { console.error(err); status.hidden = false; status.textContent = "Não foi possível carregar o modelo 3D. Recarregue a página para tentar de novo."; };
// apartamento sem o jantar + a peça de jantar escolhida (A, B aberta/fechada ou C)
let dmodel = null, tableOpen = true;
function loadModel(p) {
  if (!renderer) return;
  status.hidden = false; status.textContent = "Carregando modelo…";
  fetchGLTF(`models3/${p}_base.json`).then(g => {
    if (current !== p) return;
    if (model) scene.remove(model);
    model = g.scene; scene.add(model); applyCeiling(); status.hidden = true;
    bakedLighting(!!g.baked);
  }).catch(fail);
  loadDining(p);
}
function loadDining(p) {
  if (!renderer) return;
  const key = dining === "rebativel" && !tableOpen ? "rebativel_fechada" : dining;
  syncDinButtons();
  fetchGLTF(`models3/${p}_${key}.json`).then(g => {
    if (current !== p) return;
    if (dmodel) scene.remove(dmodel);
    dmodel = g.scene; scene.add(dmodel);
  }).catch(fail);
}
const vdin = document.getElementById("vdin");
vdin.innerHTML = Object.entries(DINING).map(([k, d]) => `<button type="button" data-vdin="${k}">${d.tag} · ${d.label}</button>`).join("") +
  `<button type="button" id="mesaopen"></button>`;
vdin.addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  if (b.id === "mesaopen") { tableOpen = !tableOpen; loadDining(current); }
  else setDining(b.dataset.vdin);
});
function syncDinButtons() {
  vdin.querySelectorAll("[data-vdin]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.vdin === dining)));
  const m = document.getElementById("mesaopen");
  m.hidden = dining !== "rebativel"; m.textContent = tableOpen ? "Fechar mesa" : "Abrir mesa";
}
function toGLB(json, bin) {
  const enc = new TextEncoder().encode(JSON.stringify(json));
  const jl = Math.ceil(enc.length / 4) * 4, bl = Math.ceil(bin.length / 4) * 4;
  const out = new Uint8Array(12 + 8 + jl + 8 + bl), dv = new DataView(out.buffer);
  dv.setUint32(0, 0x46546C67, true); dv.setUint32(4, 2, true); dv.setUint32(8, out.length, true);
  dv.setUint32(12, jl, true); dv.setUint32(16, 0x4E4F534A, true);
  out.fill(0x20, 20, 20 + jl); out.set(enc, 20);
  dv.setUint32(20 + jl, bl, true); dv.setUint32(24 + jl, 0x004E4942, true);
  out.set(bin, 28 + jl);
  return out.buffer;
}
document.getElementById("ceiling").addEventListener("click", e => {
  showCeiling = !showCeiling; e.currentTarget.setAttribute("aria-pressed", String(showCeiling));
  e.currentTarget.textContent = showCeiling ? "Esconder teto" : "Mostrar teto"; applyCeiling();
});
document.getElementById("reset").addEventListener("click", home);
document.getElementById("top").addEventListener("click", () => { exitRoom(); flyTo(new THREE.Vector3(2.1, 14, 3.85), CENTER.clone()); });
document.querySelectorAll("[data-room]").forEach(b => b.addEventListener("click", () => { if (renderer) enterRoom(b.dataset.room); }));

if (window.THREE && THREE.GLTFLoader && THREE.OrbitControls) {
  try { initViewer(); } catch (e) { status.textContent = "Seu navegador não abriu o visualizador 3D (WebGL indisponível)."; }
} else { status.textContent = "O visualizador 3D não carregou. Recarregue a página."; }
setPalette(current);
