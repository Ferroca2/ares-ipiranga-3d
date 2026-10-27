/* ---------- catálogo de móveis e eletrodomésticos ---------- */
const CATALOG = __CATALOG__;
const catGrid = document.getElementById("catgrid"), catFilter = document.getElementById("catfilter");
const cm = v => Math.round(v * 100).toLocaleString("pt-BR");
let catRoom = "Todos";

function dimsHTML(it) {
  const rows = [["Largura", it.w], ["Profundidade", it.d], ["Altura", it.h]].map(([k, v]) => `<tr><td>${k}</td><td>${cm(v)} cm</td></tr>`).join("");
  const inst = it.z0 > 0.05 ? `<tr><td>Instalação</td><td>a ${cm(it.z0)} cm do piso</td></tr>` : "";
  return `<table class="dims">${rows}${inst}</table>`;
}
function renderCatalog() {
  const rooms = ["Todos", ...new Set(CATALOG.map(i => i.room))];
  catFilter.innerHTML = rooms.map(r => `<button class="tool" type="button" data-cat="${r}" aria-pressed="${r === catRoom}">${r}</button>`).join("");
  catGrid.innerHTML = CATALOG.filter(i => catRoom === "Todos" || i.room === catRoom).map(it => `
    <article class="item">
      <button class="itemimg" type="button" data-item="${it.id}" aria-label="Ver ${it.name} em 3D">
        <img src="img2/cat_${it.id}.webp" alt="" loading="lazy" width="960" height="760"><span class="label">ver em 3D</span>
      </button>
      <div class="itemtxt">
        <span class="label">${it.room} · ${it.type}</span>
        <h3>${it.name}</h3>
        ${dimsHTML(it)}
        ${it.note ? `<p>${it.note}</p>` : ""}
      </div>
    </article>`).join("");
}
catFilter.addEventListener("click", e => { const b = e.target.closest("[data-cat]"); if (b) { catRoom = b.dataset.cat; renderCatalog(); } });
catGrid.addEventListener("click", e => { const b = e.target.closest("[data-item]"); if (b) openItem(b.dataset.item); });
renderCatalog();

// visualizador da peça, com cotas de largura, profundidade e altura
const dlg = document.getElementById("itemdlg"), ibox = document.getElementById("itemview"), istat = document.getElementById("itemstatus");
let iR, iS, iC, iCtl, iObj;
const iCache = {};
function initItemViewer() {
  iR = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  iR.setPixelRatio(Math.min(devicePixelRatio, 2));
  iR.outputEncoding = THREE.sRGBEncoding; iR.toneMapping = THREE.ACESFilmicToneMapping; iR.toneMappingExposure = 1.0;
  ibox.prepend(iR.domElement);
  iS = new THREE.Scene();
  iC = new THREE.PerspectiveCamera(30, 1, 0.01, 100);
  iS.add(new THREE.HemisphereLight(0xfffaf2, 0x6f675e, 0.75));
  const k = new THREE.DirectionalLight(0xfff1e0, 0.9); k.position.set(-3, 6, 4); iS.add(k);
  const f = new THREE.DirectionalLight(0xdfe8ff, 0.3); f.position.set(4, 3, -3); iS.add(f);
  iCtl = new THREE.OrbitControls(iC, iR.domElement); iCtl.enableDamping = true;
  new ResizeObserver(() => { const w = ibox.clientWidth, h = ibox.clientHeight; iR.setSize(w, h, false); iC.aspect = w / h; iC.updateProjectionMatrix(); }).observe(ibox);
  (function loop() { requestAnimationFrame(loop); if (dlg.open) { iCtl.update(); iR.render(iS, iC); } })();
}
function textSprite(text, color) {
  const c = document.createElement("canvas"), g = c.getContext("2d");
  c.width = 256; c.height = 80;
  g.font = "500 40px 'IBM Plex Mono', Menlo, monospace";
  const w = g.measureText(text).width + 28;
  g.fillStyle = "rgba(255,255,255,.92)"; g.fillRect((256 - w) / 2, 12, w, 56);
  g.fillStyle = color; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(text, 128, 41);
  const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, transparent: true }));
  s.renderOrder = 5;
  return s;
}
// linha de cota com traços nas pontas, afastada da peça
function dimLine(a, b, tickDir, text, size) {
  const g = new THREE.Group(), col = 0x2b55c8, m = new THREE.LineBasicMaterial({ color: col, depthTest: false });
  const t = tickDir.clone().multiplyScalar(size * 0.035);
  const pts = [a, b, a.clone().sub(t), a.clone().add(t), b.clone().sub(t), b.clone().add(t)];
  const geo = new THREE.BufferGeometry().setFromPoints([pts[0], pts[1], pts[2], pts[3], pts[4], pts[5]]);
  const l = new THREE.LineSegments(geo, m); l.renderOrder = 4; g.add(l);
  const s = textSprite(text, "#2B55C8"); s.position.copy(a).add(b).multiplyScalar(0.5).addScaledVector(tickDir, size * 0.07);
  s.scale.set(size * 0.24, size * 0.075, 1); g.add(s);
  return g;
}
function showItem(it, gltf) {
  if (iObj) iS.remove(iObj);
  const obj = new THREE.Group(), m = gltf.scene.clone();
  m.traverse(o => [].concat(o.material || []).forEach(mt => {
    if (/^Vidro/.test(mt.name)) Object.assign(mt, { transparent: true, opacity: 0.25, depthWrite: false });
  }));
  obj.add(m);
  const bb = new THREE.Box3().setFromObject(m), c = bb.getCenter(new THREE.Vector3());
  m.position.set(-c.x, -bb.min.y, -c.z);
  const sz = bb.getSize(new THREE.Vector3()), big = Math.max(sz.x, sz.y, sz.z);
  // largura ao longo da parede: x quando a frente aponta para n/s, z quando aponta para e/w
  const front = { n: [0, 0, -1], s: [0, 0, 1], e: [1, 0, 0], w: [-1, 0, 0] }[it.face];
  const F = new THREE.Vector3(...front), alongX = it.face === "n" || it.face === "s";
  const hx = sz.x / 2, hz = sz.z / 2, off = big * 0.08;
  const W = alongX ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 0, 1);
  const halfW = alongX ? hx : hz, halfD = alongX ? hz : hx;
  const frontEdge = F.clone().multiplyScalar(halfD + off);
  obj.add(dimLine(W.clone().multiplyScalar(-halfW).add(frontEdge), W.clone().multiplyScalar(halfW).add(frontEdge), F, `${cm(it.w)} cm`, big));
  const side = W.clone().multiplyScalar(halfW + off);
  obj.add(dimLine(side.clone().addScaledVector(F, -halfD), side.clone().addScaledVector(F, halfD), W, `${cm(it.d)} cm`, big));
  const corner = W.clone().multiplyScalar(-halfW - off).addScaledVector(F, halfD);
  obj.add(dimLine(corner.clone(), corner.clone().setY(sz.y), W.clone().negate(), `${cm(it.h)} cm`, big));
  iObj = obj; iS.add(obj);
  const dir = F.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), 0.6).setY(0.55).normalize();
  iCtl.target.set(0, sz.y / 2, 0);
  iC.position.copy(iCtl.target).addScaledVector(dir, big * 2.6);
  iCtl.minDistance = big * 0.8; iCtl.maxDistance = big * 6; iCtl.update();
  istat.hidden = true;
}
function openItem(id) {
  const it = CATALOG.find(i => i.id === id);
  document.getElementById("itemname").textContent = it.name;
  document.getElementById("itemmeta").textContent = `${it.room} · ${it.type}`;
  document.getElementById("itemdims").innerHTML = dimsHTML(it) + (it.note ? `<p>${it.note}</p>` : "");
  dlg.showModal();
  if (!iR) { try { initItemViewer(); } catch (e) { istat.hidden = false; istat.textContent = "Seu navegador não abriu o 3D."; return; } }
  if (iObj) { iS.remove(iObj); iObj = null; }
  if (iCache[id]) return showItem(it, iCache[id]);
  istat.hidden = false; istat.textContent = "Carregando peça…";
  fetch(`items/${id}.json`).then(r => r.json()).then(json => {
    const b64 = json.buffers[0].uri.split(",")[1];
    const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    delete json.buffers[0].uri;
    new THREE.GLTFLoader().parse(toGLB(json, bin), "", g => { iCache[id] = g; if (dlg.open) showItem(it, g); }, () => { istat.textContent = "Não foi possível carregar a peça."; });
  }).catch(() => { istat.textContent = "Não foi possível carregar a peça."; });
}
document.getElementById("itemclose").addEventListener("click", () => dlg.close());
dlg.addEventListener("click", e => { if (e.target === dlg) dlg.close(); });
