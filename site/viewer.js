/* ---------- viewer 3D ---------- */
const box = document.getElementById("viewer"), status = document.getElementById("status");
let renderer, scene, camera, controls, model, showCeiling = false;
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
  home();
  new ResizeObserver(resize).observe(box); resize();
  (function loop() { requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera); })();
}
function resize() {
  const w = box.clientWidth, h = box.clientHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
}
function home() { camera.position.set(8.5, 9, 12.5); controls.target.copy(CENTER); controls.update(); }
function applyCeiling() {
  if (!model) return;
  model.traverse(o => { if (/^(Teto|Sanca)/.test(o.name)) o.visible = showCeiling; });
}
function loadModel(p) {
  if (!renderer) return;
  const show = gltf => {
    if (current !== p) return;
    if (model) scene.remove(model);
    model = gltf.scene; scene.add(model); applyCeiling(); status.hidden = true;
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
document.getElementById("top").addEventListener("click", () => { camera.position.set(2.1, 14, 3.85); controls.target.copy(CENTER); controls.update(); });

if (window.THREE && THREE.GLTFLoader && THREE.OrbitControls) {
  try { initViewer(); } catch (e) { status.textContent = "Seu navegador não abriu o visualizador 3D (WebGL indisponível)."; }
} else { status.textContent = "O visualizador 3D não carregou. Recarregue a página."; }
setPalette(current);
