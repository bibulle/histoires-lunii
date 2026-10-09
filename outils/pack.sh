#!/bin/sh
# Fabrique le pack Lunii (archive STUdio) : pack/Les-Aventures-des-Princesses.zip
# Usage : sh outils/pack.sh             (fabriquer le pack)
#         sh outils/pack.sh --liste     (voir ce qui serait fait et ce qui manque)
#         sh outils/pack.sh --incomplet (le faire même s'il manque des sons)
cd "$(dirname "$0")/.."
PY="$HOME/omnivoice-env/bin/python"
[ -x "$PY" ] || PY=python3
exec "$PY" -u outils/generer_pack.py "$@"
