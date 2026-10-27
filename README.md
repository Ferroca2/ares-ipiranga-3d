# Ares Ipiranga · final 01 — Ateliê Ipiranga

Estudo de interiores em 3D para o apartamento final 01/08 (31,22 m², 2 dormitórios) do Ares Ipiranga (Brio), modelado a partir da planta de contrato.

- **Site:** pasta `web/` (renders das 5 paletas, planta cotada, modelo 3D interativo com passeio pelos cômodos, catálogo de móveis com medidas)
- **Caderno A3:** `Ares_Ipiranga_Atelie_Projeto3D.pdf`
- **Modelos 3D (.blend, .fbx, .obj, .dae, .glb):** na [Release v2](../../releases/tag/v2)
- **Pesquisa e conceito:** `research/design_brief.md`

## Como regerar
Blender 4.2 como módulo Python (`pip install bpy==4.2.0`, Python 3.11):

```sh
python fetch_assets.py                                   # texturas/modelos CC0 do Poly Haven
python build2.py --palette terra --views all --samples 160 --export glb,fbx,obj,dae
python light_glb.py terra                                # GLB leve para o visualizador web
python deliverables2.py && python3 merge_site.py         # PDF, imagens e página
```

Medidas internas da planta de contrato, sujeitas ao projeto executivo. Texturas, céu e objetos: Poly Haven (CC0).
