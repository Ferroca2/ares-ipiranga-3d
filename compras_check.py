"""Confere os links da pesquisa de compras: abre cada um como um navegador e anota se está no ar.

ok = True (abriu, sem aviso de indisponível), False (404, página removida ou produto esgotado) ou
None (a loja bloqueou o acesso automático: precisa ser conferido no navegador).

uso: python compras_check.py <pasta com os JSONs> <saída.json>
"""
import concurrent.futures as cf, json, os, re, sys, urllib.error, urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")
GONE = re.compile(r"(produto (indispon[ií]vel|esgotado)|fora de estoque|an[uú]ncio (pausado|finalizado)|"
                  r"p[aá]gina n[aã]o (foi )?encontrada|currently unavailable|esta publica[cç][aã]o (est[aá] )?pausada|"
                  r"este produto n[aã]o est[aá] mais dispon[ií]vel|avise-me quando chegar|atualmente indispon[ií]vel)", re.I)

BOT = re.compile(r"(account-verification|captcha|validateCaptcha|Digite os caracteres|/gz/|suspicious-traffic)", re.I)


def check(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9",
                                               "Accept": "text/html,application/xhtml+xml"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read(1_500_000).decode("utf-8", "replace")
            final = r.geturl()
            if BOT.search(final) or BOT.search(body[:200_000]) and len(body) < 60_000:
                return dict(ok=None, status=r.status, final=final, motivo="verificação anti-robô")
            m = GONE.search(body)
            return dict(ok=not m, status=r.status, final=final, motivo=m.group(0) if m else "")
    except urllib.error.HTTPError as e:
        return dict(ok=False if e.code in (404, 410) else None, status=e.code, motivo=f"HTTP {e.code}")
    except Exception as e:  # noqa: BLE001
        return dict(ok=None, status=0, motivo=str(e)[:120])


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    urls = set()
    for f in os.listdir(src):
        if f.endswith(".json") and not f.startswith("_"):
            for it in json.load(open(os.path.join(src, f))).values():
                for ops in (it.get("variantes") or {}).values():
                    urls |= {o["url"] for o in ops if o.get("url")}
    with cf.ThreadPoolExecutor(6) as ex:
        res = dict(zip(sorted(urls), ex.map(check, sorted(urls))))
    json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
    for k in (True, None, False):
        print({True: "ok", None: "bloqueado (conferir no navegador)", False: "quebrado"}[k],
              sum(r["ok"] is k for r in res.values()))
    for u, r in res.items():
        if r["ok"] is not True:
            print(" ", "X" if r["ok"] is False else "?", r["motivo"], u)
