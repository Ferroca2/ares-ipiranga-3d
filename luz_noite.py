"""Luz pré-calculada do modelo 3D do site, em resolução alta, para rodar à noite em outro computador.

Monta as cenas (.blend) se faltarem, calcula a luz de cada paleta e opção de jantar, um cálculo por vez
com pausa entre eles, e grava o resultado em web/models3 (a pasta que a Vercel publica).
Pode ser interrompido: na próxima vez continua de onde parou. Guia completo em LUZ_NOITE.md.

uso: python luz_noite.py [--tamanho 2048] [--amostras 32] [--gpu] [--pausa 120] [--paletas terra,mata] [--publicar]
"""
import argparse, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
PALETAS = ["terra", "mata", "moderno", "ipe", "ebano"]
JANTAR = ["rebativel", "rebativel_fechada", "bancada", "centro", "parede", "parede_fechada"]

ap = argparse.ArgumentParser()
ap.add_argument("--tamanho", type=int, default=2048, help="lado do mapa de luz do apartamento, em px (site atual: 1024)")
ap.add_argument("--amostras", type=int, default=32, help="amostras por pixel (mais = menos granulado e mais lento)")
ap.add_argument("--gpu", action="store_true", help="usa a placa de vídeo (sem isso, só o processador)")
ap.add_argument("--pausa", type=int, default=120, help="segundos de descanso entre um cálculo e outro")
ap.add_argument("--paletas", default=",".join(PALETAS))
ap.add_argument("--publicar", action="store_true", help="no fim faz commit e push de web/models3")
a = ap.parse_args()
pals = a.paletas.split(",")
LOG = os.path.join(ROOT, "logs", "luz_noite")
os.makedirs(LOG, exist_ok=True)


def say(*m):
    print(time.strftime("%H:%M"), *m, flush=True)


def calma():
    time.sleep(a.pausa)
    # no Mac, espera o processador sair do limite térmico antes do próximo cálculo
    while sys.platform == "darwin":
        t = subprocess.run(["pmset", "-g", "therm"], capture_output=True, text=True).stdout
        m = re.search(r"CPU_Speed_Limit\s*=\s*(\d+)", t)
        if not m or int(m.group(1)) >= 100:
            break
        say("  esfriando…")
        time.sleep(120)


def run(nome, args, ok):
    """Roda um passo num processo próprio (a memória volta toda ao sistema no fim). ok: texto que o log precisa ter."""
    marca = os.path.join(LOG, nome + ".ok")
    if os.path.exists(marca):
        say("já feito:", nome)
        return True
    calma()
    say("começando:", nome)
    t0 = time.time()
    with open(os.path.join(LOG, nome + ".log"), "w") as f:
        subprocess.run([PY, *args], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
    txt = open(os.path.join(LOG, nome + ".log"), errors="replace").read()
    if ok in txt:
        open(marca, "w").close()
        say(f"  ok em {(time.time() - t0) / 60:.0f} min")
        return True
    say(f"  FALHOU (veja logs/luz_noite/{nome}.log); segue para o próximo")
    return False


def blend(p, o=None):
    return os.path.join("modelo2", p, f"jantar_{o}.blend" if o else f"ares_ipiranga_final01_{p}.blend")


# 1. texturas CC0 do Poly Haven (só na primeira vez)
if not os.path.isdir(os.path.join(ROOT, "assets", "ph", "textures")):
    say("baixando texturas do Poly Haven…")
    subprocess.run([PY, "fetch_assets.py"], cwd=ROOT, check=True)

# 2. cenas .blend que faltarem (o apartamento com a opção B e uma cena por opção de jantar)
for p in pals:
    for o in [None] + JANTAR:
        if not os.path.exists(os.path.join(ROOT, blend(p, o))):
            run(f"cena_{p}_{o or 'base'}", ["build2.py", "--palette", p, "--dining", o or "rebativel",
                                            "--save", blend(p, o)], "SAVED")

# 3. luz: o apartamento em cada paleta; o jantar só na terra, as outras reaproveitam (mesma geometria)
dev = ["--lm-device", "GPU" if a.gpu else "CPU", "--lm-samples", str(a.amostras)]
for p in (["terra"] + [q for q in pals if q != "terra"]) if "terra" in pals else pals:
    run(f"luz_{p}_base", ["light_glb.py", p, "--part", "base", "--out", f"modelo2/{p}/web/base.glb",
                          "--lightmap", "--lm-size", str(a.tamanho), *dev], "OCCLUSION")
    for o in JANTAR:
        extra = ["--lm-size", str(a.tamanho // 2)]
        if p != "terra":
            npy = os.path.join("web_tex", "terra", f"lightmap_dining_{o}.npy")
            if not os.path.exists(os.path.join(ROOT, npy)):
                say(f"  pulando {p} {o}: falta a luz do jantar da terra")
                continue
            extra = ["--lm-size", str(a.tamanho // 2), "--lm-from", npy]
        run(f"luz_{p}_{o}", ["light_glb.py", p, "--part", "dining", "--blend", blend(p, o),
                             "--out", f"modelo2/{p}/web/{o}.glb", "--lightmap", *extra, *dev], "OCCLUSION")

# 4. GLB -> JSON que o visualizador lê, direto na pasta publicada
from deliverables2 import glb_to_json  # noqa: E402
feitos = []
for p in pals:
    wd = os.path.join(ROOT, "modelo2", p, "web")
    for f in sorted(os.listdir(wd)) if os.path.isdir(wd) else []:
        if f.endswith(".glb") and os.path.exists(os.path.join(LOG, f"luz_{p}_{f[:-4]}.ok")):
            for d in ("web", "site"):
                os.makedirs(os.path.join(ROOT, d, "models3"), exist_ok=True)
                glb_to_json(os.path.join(wd, f), os.path.join(ROOT, d, "models3", f"{p}_{f[:-4]}.json"))
            feitos.append(f"{p}_{f[:-4]}")
say(f"{len(feitos)} modelos atualizados em web/models3")

if a.publicar and feitos:
    subprocess.run(["git", "add", "web/models3"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", f"Luz do modelo 3D em {a.tamanho} px ({len(feitos)} modelos)"], cwd=ROOT)
    subprocess.run(["git", "push"], cwd=ROOT)
    say("publicado; a Vercel atualiza o site em poucos minutos")
say("FIM")
