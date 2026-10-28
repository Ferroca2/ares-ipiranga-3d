# Luz do modelo 3D em alta resolução: rodar à noite em outro computador

Isto melhora a luz do **modelo 3D interativo do site**: sombras, cantos e claridade da janela ficam mais definidos ao passear pelo apartamento.
As **fotos** (renders) e o **vídeo** não mudam, porque já são calculados com luz completa.

O script `luz_noite.py` faz tudo sozinho:

1. Baixa as texturas e monta as cenas do Blender.
2. Calcula a luz das 5 paletas e das 6 variações de jantar. Faz um cálculo por vez, com pausa entre eles.
3. Grava o resultado em `web/models3`.
4. Com `--publicar`, envia para o GitHub e a Vercel atualiza o site.

## Do que o computador precisa

- **Python 3.11** (precisa ser exatamente a versão 3.11, porque o Blender 4.2 não funciona com outras).
- **Git**, com permissão de envio para este repositório. Basta para usar `--publicar`.
- **Memória:** 16 GB de RAM recomendados. Com 8 GB, use `--tamanho 1536`.
- **Disco:** cerca de 5 GB livres.
- Windows, Mac ou Linux.

## Preparar (uma vez)

**Mac / Linux**
```sh
git clone https://github.com/Ferroca2/ares-ipiranga-3d.git
cd ares-ipiranga-3d
python3.11 -m venv .venv
.venv/bin/pip install bpy==4.2.0 pillow reportlab
```

**Windows (PowerShell)**
```powershell
git clone https://github.com/Ferroca2/ares-ipiranga-3d.git
cd ares-ipiranga-3d
py -3.11 -m venv .venv
.venv\Scripts\pip install bpy==4.2.0 pillow reportlab
```

## Rodar à noite

**Mac / Linux**
```sh
.venv/bin/python luz_noite.py --publicar
```

**Windows**
```powershell
.venv\Scripts\python luz_noite.py --publicar
```

Para não suspender durante a noite:

- **Mac:** rode com `caffeinate -i` na frente do comando.
- **Windows:** em Configurações → Energia, defina "Suspender" como "Nunca".

### Opções

| opção | padrão | o que faz |
|---|---|---|
| `--tamanho` | `2048` | Resolução da luz do apartamento. O site usa 1024 hoje; o jantar usa metade desse valor. |
| `--amostras` | `32` | Qualidade de cada ponto. Use 64 para menos granulado, mas leva o dobro do tempo. |
| `--gpu` | desligado | Usa a placa de vídeo (NVIDIA, AMD ou Intel no Windows/Linux). **Num Mac, não use:** travou o Blender. Sem placa compatível, usa o processador. |
| `--pausa` | `120` | Segundos de descanso entre um cálculo e outro. No Mac, também espera o processador esfriar. |
| `--paletas` | todas | Exemplo: `--paletas terra,mata`. A terra precisa ser feita antes, porque as outras reaproveitam o jantar dela. |
| `--publicar` | desligado | No fim, faz commit e push de `web/models3`. |

### Exemplos

Placa NVIDIA, qualidade máxima:
```sh
.venv/bin/python luz_noite.py --gpu --amostras 128 --publicar
```

Teste rápido só com a terra, sem publicar:
```sh
.venv/bin/python luz_noite.py --paletas terra --tamanho 1024
```

## Quanto demora

- **Só no processador**, num notebook parecido com o Mac deste projeto: de 6 a 8 horas com o padrão. Para comparar, a versão atual do site (1024 px, 32 amostras) levou uns 16 minutos por paleta.
- **Com `--gpu`** numa placa NVIDIA recente: costuma ficar em 1 a 2 horas.
- **Primeira vez:** soma uns 30–40 minutos para baixar as texturas e montar as cenas.

## Se parar no meio

Basta rodar o mesmo comando de novo: o script pula o que já terminou.

- **Onde ficam as marcas e os logs:** `logs/luz_noite/`.
- **Se um cálculo falhar** (por exemplo, falta de memória), o script avisa, segue para o próximo e não publica aquele modelo. Ele continua com a luz atual no site.
- **Para recomeçar do zero:** apague `logs/luz_noite/`.

## Conferir antes de publicar

Sem `--publicar`, os modelos novos ficam em `web/models3` e você pode olhar no navegador antes de enviar:

```sh
cd web && python3 -m http.server 8000
```

Depois abra http://localhost:8000. Para publicar em seguida:

```sh
git add web/models3 && git commit -m "Luz do modelo 3D em alta resolução" && git push
```
