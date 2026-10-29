/* ---------- catálogo de móveis e eletrodomésticos ---------- */
const CATALOG = __CATALOG__;
const COMPRAS = __COMPRAS__;
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
  // peças do jantar só aparecem na opção escolhida
  const tag = DINING[dining].tag;
  catGrid.innerHTML = CATALOG.filter(i => (catRoom === "Todos" || i.room === catRoom) && (!i.opts || i.opts.includes(tag))).map(it => `
    <article class="item">
      <button class="itemimg" type="button" data-item="${it.id}" aria-label="Ver ${it.name} em 3D">
        <img src="img2/cat_${it.id}.webp" alt="" loading="lazy" width="960" height="760"><span class="label">ver em 3D</span>
      </button>
      <div class="itemtxt">
        <span class="label">${it.room}${it.opts && it.opts.length < 3 ? ` · opção ${it.opts.split("").join("/")}` : ""} · ${it.type}</span>
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
  document.getElementById("itembuy").innerHTML = buyHTML(it);
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


/* ---------- onde comprar: 3 opções por peça, na cor da paleta em uso ---------- */
const PARTE = { cuba: "Cuba", torneira: "Torneira", box: "Cama box + colchão", roupa: "Roupa de cama", peseira: "Peseira",
  vidracaria: "Vidraçarias (sob medida, até o forro)", kit: "Kit pronto (mais barato, até 1,90 m)", pronto: "Pronto, sem marcenaria" };
const PREST = { marcenaria: "Marcenarias (sob medida)", estofador: "Estofadores", palhinha: "Tela de palhinha" };
const brl = v => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: 2 });
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
function optsFor(key) {
  const it = COMPRAS.itens[key];
  if (!it) return null;
  const v = it.paletas[current] || Object.keys(it.variantes)[0];
  return { ops: it.variantes[v] || [], dica: it.dica };
}
function optHTML(o) {
  const meta = [o.preco != null ? `<b>${brl(o.preco)}</b>` : "", o.nota != null ? `★ ${String(o.nota).replace(".", ",")}${o.avaliacoes ? ` (${o.avaliacoes.toLocaleString("pt-BR")})` : ""}` : ""].filter(Boolean).join(" · ");
  const sub = [o.cor, o.medidas].filter(Boolean).map(esc).join(" · ");
  return `<li><a href="${esc(o.url)}" target="_blank" rel="noopener nofollow"><span class="shop">${esc(o.loja)}</span>${esc(o.produto || "")}</a>
    ${meta ? `<span class="meta">${meta}</span>` : ""}${sub ? `<span class="sub">${sub}</span>` : ""}${o.obs ? `<details class="sub"><summary>detalhes</summary>${esc(o.obs)}</details>` : ""}</li>`;
}
function groupHTML(title, g) {
  if (!g || !g.ops.length) return "";
  return `${title ? `<h4>${title}</h4>` : ""}<ol class="buylist">${g.ops.map(optHTML).join("")}</ol>${g.dica ? `<details class="dica"><summary>dica de compra</summary>${esc(g.dica)}</details>` : ""}`;
}
function buyHTML(it) {
  const keys = Object.keys(COMPRAS.itens).filter(k => k === it.id || k.startsWith(it.id + ":"));
  let h = keys.map(k => groupHTML(k.includes(":") ? PARTE[k.split(":")[1]] || k.split(":")[1] : "", optsFor(k))).join("");
  if (it.type === "Marcenaria") h += ["marcenaria", ...(COMPRAS.extra[it.id] || [])].map(k => groupHTML(PREST[k], optsFor(k))).join("");
  if (!h) return "";
  return `<div class="buy"><span class="label">onde comprar · ${PALETTES[current].label}</span>${h}<p class="dica">Preços e notas conferidos em out/2026; podem mudar. Ordem: do mais barato ao mais caro.</p></div>`;
}

function renderFinishes() {
  const box = document.getElementById("acabgrid");
  if (!box) return;
  document.getElementById("acabpal").textContent = PALETTES[current].label;
  box.innerHTML = COMPRAS.acabamentos.filter(a => COMPRAS.itens[a.id]).map(a => `
    <article class="acab">
      <div class="acabhead">${a.hex ? `<i class="swatch" style="background:${a.hex[current]}" title="${a.hex[current]}"></i>` : ""}
        <div><span class="label">${a.onde}</span><h3>${a.nome}</h3>${a.hex ? `<code>${a.hex[current]}</code>` : ""}</div></div>
      ${groupHTML("", optsFor(a.id))}
    </article>`).join("");
  const pr = document.getElementById("prestgrid");
  if (pr) pr.innerHTML = Object.keys(PREST).filter(k => COMPRAS.itens[k]).map(k => `<article class="acab"><h3>${PREST[k]}</h3>${groupHTML("", optsFor(k))}</article>`).join("");
}
window.comprasReady = true;
renderFinishes();

/* ---------- quanto custa tudo: total de cada combinação de opções, na paleta e opção de jantar em uso ---------- */
// quantidades: peças em par, área de piso/revestimento com 10% de perda, latas de tinta, cortinas da sala e do quarto
const QTD = { cadeira: 2, banqueta: 2, banco_baixo: 2, arandela: 2, "criado:pronto": 2, "ripado:pronto": 3, cortina: 2,
  tinta_parede: 2, piso_vinilico: 26, porcelanato_banho: 4, azulejo_box: 5.5, azulejo_cozinha: 1.2 };
const UNID = { piso_vinilico: "m²", porcelanato_banho: "m²", azulejo_box: "m²", azulejo_cozinha: "m²", tinta_parede: "latas" };
// gráfico 1: tudo cotado (a marcenaria entra pelas alternativas prontas); gráfico 2: sem nada de madeira planejada,
// que vai para a marcenaria sob medida (cuba e torneira do gabinete continuam, porque são compradas à parte)
const COSTS = [{ id: "", skip: () => false },
  { id: "2", skip: (k, cat) => k in PREST || (cat && cat.type === "Marcenaria" && !["cuba", "torneira"].includes(k.split(":")[1])) }];
function costPieces(C) {
  const tag = DINING[dining].tag, out = [];
  for (const k of Object.keys(COMPRAS.itens)) {
    const base = k.split(":")[0], part = k.split(":")[1];
    const cat = CATALOG.find(i => i.id === base), fin = COMPRAS.acabamentos.find(a => a.id === k);
    if (cat && cat.opts && !cat.opts.includes(tag)) continue;
    if (!cat && !fin && !(k in PREST)) continue;
    if (C.skip(k, cat)) continue;
    const g = optsFor(k), ops = g ? g.ops.filter(o => o.preco != null) : [];
    if (!ops.length) continue;
    const nome = cat ? cat.name + (part ? ` · ${part === "pronto" ? "pronto" : (PARTE[part] || part).split(" (")[0]}` : "") : fin ? fin.nome : PREST[k];
    out.push({ k, nome, q: QTD[k] || 1, ops });
  }
  return out;
}
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const $c = (C, id) => document.getElementById(id + C.id);
function renderCost() { COSTS.forEach(renderCostChart); }
function renderCostChart(C) {
  const box = $c(C, "costplot");
  if (!box) return;
  const P = costPieces(C), n = P.length, N = 20000, SHOW = 400, rnd = rng(31);
  const pick = new Uint8Array(N * n), tot = new Float64Array(N);
  for (let s = 0; s < N; s++) for (let j = 0; j < n; j++) {
    const i = Math.floor(rnd() * P[j].ops.length); pick[s * n + j] = i; tot[s] += P[j].ops[i].preco * P[j].q;
  }
  // extremos exatos: a mais barata e a mais cara de cada peça
  const ext = f => P.map(p => p.ops.reduce((b, o, i) => f(o.preco, p.ops[b].preco) ? i : b, 0));
  const lo = ext((a, b) => a < b), hi = ext((a, b) => a > b);
  const sumOf = c => c.reduce((s, i, j) => s + P[j].ops[i].preco * P[j].q, 0);
  const order = Array.from(tot.keys()).sort((a, b) => tot[a] - tot[b]);
  const mean = P.reduce((s, p) => s + p.q * p.ops.reduce((a, o) => a + o.preco, 0) / p.ops.length, 0);
  const med = (tot[order[N / 2 - 1]] + tot[order[N / 2]]) / 2;
  const pts = [];
  for (let r = 0; r < SHOW; r++) {
    if (r === 0) { pts.push({ c: lo, t: sumOf(lo), pct: 0 }); continue; }
    if (r === SHOW - 1) { pts.push({ c: hi, t: sumOf(hi), pct: 100 }); continue; }
    const s = order[Math.round(r / (SHOW - 1) * (N - 1))];
    pts.push({ c: Array.from(pick.subarray(s * n, s * n + n)), t: tot[s], pct: r / (SHOW - 1) * 100 });
  }
  const combos = P.reduce((m, p) => m * p.ops.length, 1);
  C.S = { P, pts, mean, med, min: pts[0].t, max: pts[SHOW - 1].t, combos };
  C.pin = -1;
  const k = v => brl(Math.round(v)).replace(/,00$/, "");
  const e = Math.floor(Math.log10(combos)), mant = (combos / 10 ** e).toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  $c(C, "costpal").textContent = `${PALETTES[current].label} · opção ${DINING[dining].tag}`;
  $c(C, "coststats").innerHTML = [["Mínimo", C.S.min], ["Mediana", med], ["Média", mean], ["Máximo", C.S.max]]
    .map(([l, v]) => `<div class="stat"><span class="label">${l}</span><b>${k(v)}</b></div>`).join("") +
    `<div class="stat"><span class="label">Combinações</span><b>${mant} × 10<sup>${e}</sup></b></div>`;
  drawCost(C);
  showCombo(C, Math.round(SHOW / 2));
}
function drawCost(C) {
  const S = C.S, box = $c(C, "costplot"), W = box.clientWidth || 800, H = Math.max(260, Math.min(420, W * 0.5));
  const m = { l: 84, r: 16, t: 16, b: 34 }, iw = W - m.l - m.r, ih = H - m.t - m.b;
  const raw = (S.max - S.min) / 5, mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map(f => f * mag).find(v => v >= raw), y0 = Math.floor(S.min / step) * step, y1 = Math.ceil(S.max / step) * step;
  const X = p => m.l + p / 100 * iw, Y = v => m.t + (1 - (v - y0) / (y1 - y0)) * ih;
  const mil = v => `R$ ${(v / 1000).toLocaleString("pt-BR", { maximumFractionDigits: step % 1000 ? 1 : 0 })} mil`;
  let g = "";
  for (let v = y0; v <= y1 + 1; v += step) g += `<line class="grid" x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}"/><text class="tick" x="${m.l - 8}" y="${Y(v) + 4}" text-anchor="end">${mil(v)}</text>`;
  for (const p of [0, 25, 50, 75, 100]) g += `<text class="tick" x="${X(p)}" y="${H - 10}" text-anchor="${p === 0 ? "start" : p === 100 ? "end" : "middle"}">${p}%</text>`;
  const dots = S.pts.map((p, i) => `<circle class="dot" data-i="${i}" cx="${X(p.pct).toFixed(1)}" cy="${Y(p.t).toFixed(1)}" r="3.5"/>`).join("");
  const ref = (v, cls, txt, dy) => `<line class="${cls}" x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}"/><text class="reflabel" x="${m.l + 8}" y="${Y(v) + dy}">${txt}</text>`;
  const k = v => brl(Math.round(v)).replace(/,00$/, "");
  box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Total de cada combinação, da mais barata à mais cara">
    ${g}${dots}${ref(S.mean, "meanline", `média ${k(S.mean)}`, S.mean >= S.med ? -7 : 16)}${ref(S.med, "medline", `mediana ${k(S.med)}`, S.med > S.mean ? -7 : 16)}
    <line class="cross" y1="${m.t}" y2="${m.t + ih}" x1="-9" x2="-9"/><circle class="hl" r="7" cx="-20" cy="-20"/>
    <rect class="hit" x="${m.l}" y="${m.t}" width="${iw}" height="${ih}" fill="transparent"/></svg><div class="costtip" hidden></div>`;
  S.X = X; S.Y = Y;
  const hit = box.querySelector(".hit"), idx = ev => {
    const r = hit.getBoundingClientRect(), pct = (ev.clientX - r.left) / r.width * 100;
    return Math.max(0, Math.min(S.pts.length - 1, Math.round(pct / 100 * (S.pts.length - 1))));
  };
  hit.addEventListener("pointermove", ev => { if (C.pin < 0) showCombo(C, idx(ev), ev); });
  hit.addEventListener("pointerdown", ev => { const i = idx(ev); C.pin = C.pin === i ? -1 : i; showCombo(C, i, ev); });
  hit.addEventListener("pointerleave", () => { box.querySelector(".costtip").hidden = true; });
}
function showCombo(C, i, ev) {
  const S = C.S, p = S.pts[i], k = v => brl(Math.round(v)).replace(/,00$/, ""), box = $c(C, "costplot");
  const cx = S.X(p.pct), cy = S.Y(p.t), hl = box.querySelector(".hl"), cr = box.querySelector(".cross");
  hl.setAttribute("cx", cx); hl.setAttribute("cy", cy); cr.setAttribute("x1", cx); cr.setAttribute("x2", cx);
  const tip = box.querySelector(".costtip");
  if (ev) {
    tip.hidden = false;
    tip.innerHTML = `<b>${k(p.t)}</b><span>${Math.round(p.pct)}% das combinações custam menos${C.pin === i ? " · fixada" : ""}</span>`;
    tip.style.left = `${Math.min(cx + 12, box.clientWidth - 230)}px`; tip.style.top = `${Math.max(0, cy - 56)}px`;
  }
  $c(C, "combohead").innerHTML = `Combinação de <b>${k(p.t)}</b> <span class="label">${i === 0 ? "a mais barata" : i === S.pts.length - 1 ? "a mais cara" : `${Math.round(p.pct)}% custam menos`}</span>`;
  $c(C, "combolist").innerHTML = S.P.map((pc, j) => {
    const o = pc.ops[p.c[j]], sub = o.preco * pc.q;
    return `<li><span class="cn">${esc(pc.nome)}${pc.q !== 1 ? ` <i>× ${String(pc.q).replace(".", ",")}${UNID[pc.k] ? " " + UNID[pc.k] : ""}</i>` : ""}</span>
      <a href="${esc(o.url)}" target="_blank" rel="noopener nofollow">${esc(o.loja)} · ${esc(o.produto || "")}</a><b>${k(sub)}</b></li>`;
  }).join("");
}
for (const C of COSTS) { const el = $c(C, "costplot"); if (el) new ResizeObserver(() => { if (C.S) drawCost(C); }).observe(el); }
renderCost();
