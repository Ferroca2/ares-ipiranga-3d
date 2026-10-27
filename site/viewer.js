/* ---------- viewer 3D ---------- */
const box = document.getElementById("viewer"), status = document.getElementById("status");
let renderer, scene, camera, controls, model, showCeiling = false, walking = false, fly = null;
const keys = new Set(), clock = new THREE.Clock(), walkhint = document.getElementById("walkhint");
// olho a 1,55 m; coordenadas do modelo: x, altura, y da planta
const ROOMS = {
  sala:     [[3.75, 1.55, 6.60], [0.40, 1.20, 5.95]],
  cozinha:  [[0.70, 1.55, 5.85], [3.70, 1.20, 7.25]],
  corredor: [[2.50, 1.55, 6.75], [2.50, 1.30, 2.60]],
  dorm1:    [[2.25, 1.55, 2.30], [0.55, 0.90, 0.30]],
  dorm2:    [[1.85, 1.55, 4.35], [0.25, 1.00, 3.05]],
  banho:    [[3.10, 1.55, 4.85], [3.95, 1.10, 3.30]],
};
const cache = {};
const CENTER = new THREE.Vector3(2.1, 0.8, 3.8);
function initViewer() {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.1;
  box.prepend(renderer.domElement);
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(38, 16 / 9, 0.05, 200);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8580, 0.9));
  const sun = new THREE.DirectionalLight(0xfff3e6, 0.9); sun.position.set(-6, 10, 4); scene.add(sun);
  const fill = new THREE.DirectionalLight(0xdfe8ff, 0.35); fill.position.set(8, 6, 10); scene.add(fill);
  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.maxPolarAngle = Math.PI * 0.49;
  controls.minDistance = 1.5; controls.maxDistance = 25;
  camera.position.set(8.5, 9, 12.5); controls.target.copy(CENTER); controls.update();
  new ResizeObserver(resize).observe(box); resize();
  box.tabIndex = 0;
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
      fly.t = Math.min(1, fly.t + dt / 1.1);
      const k = fly.t < 0.5 ? 2 * fly.t * fly.t : 1 - Math.pow(-2 * fly.t + 2, 2) / 2;
      camera.position.lerpVectors(fly.p0, fly.p1, k); controls.target.lerpVectors(fly.t0, fly.t1, k);
      if (fly.t === 1) fly = null;
    } else if (walking && keys.size) walk(dt);
    controls.update(); renderer.render(scene, camera);
  })();
}
function resize() {
  const w = box.clientWidth, h = box.clientHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
}
function flyTo(pos, target) {
  fly = { t: 0, p0: camera.position.clone(), t0: controls.target.clone(), p1: pos, t1: target };
}
function exitRoom() {
  if (!walking) return;
  walking = false; keys.clear(); walkhint.hidden = true; scene.background = null;
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
  document.querySelectorAll("[data-room]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.room === name)));
  applyCeiling();
  flyTo(eye, eye.clone().add(look.sub(eye).normalize().multiplyScalar(0.01)));
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
function loadModel(p) {
  if (!renderer) return;
  const show = gltf => {
    if (current !== p) return;
    if (model) scene.remove(model);
    model = gltf.scene; scene.add(model); applyCeiling(); status.hidden = true;
    model.traverse(o => [].concat(o.material || []).forEach(m => {
      if (/^Vidro/.test(m.name)) Object.assign(m, { transparent: true, opacity: m.name === "Vidro" ? 0.12 : 0.45, metalness: 0, roughness: 0.05, depthWrite: false });
    }));
  };
  if (cache[p]) return show(cache[p]);
  status.hidden = false; status.textContent = "Carregando modelo…";
  const fail = err => { console.error(err); status.hidden = false; status.textContent = "Não foi possível carregar o modelo 3D. Recarregue a página para tentar de novo."; };
  fetch(`models/${p}.json`).then(r => r.json()).then(json => {
    // o frame bloqueia URLs data:, então o buffer embutido vira um GLB montado em memória
    const b64 = json.buffers[0].uri.split(",")[1];
    const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    delete json.buffers[0].uri;
    new THREE.GLTFLoader().parse(toGLB(json, bin), "", g => { cache[p] = g; show(g); }, fail);
  }).catch(fail);
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
