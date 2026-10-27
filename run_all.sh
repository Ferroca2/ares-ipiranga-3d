#!/bin/zsh
cd "$(dirname "$0")"
for p in terracota nordico grafite petroleo; do
  fmt=glb
  [[ $p == terracota ]] && fmt=glb,fbx,obj,dae,stl
  .venv/bin/python build.py --palette $p --views all --samples 64 --export $fmt 2>&1 | grep -E "^OK|EXPORT|Error|Traceback|rror:" 
done
echo ALL DONE
