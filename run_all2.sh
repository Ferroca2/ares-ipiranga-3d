#!/bin/zsh
cd "$(dirname "$0")"
for p in terra mata moderno ipe; do
  fmt=glb
  [[ $p == terra ]] && fmt=glb,fbx,obj,dae
  .venv/bin/python build2.py --palette $p --views all --samples 160 --export $fmt 2>&1 | grep -E "^OK|EXPORT|Error|Traceback|rror:"
done
echo ALL DONE
