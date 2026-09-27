#!/bin/sh
# Génère toutes les voix pendant la nuit, en empêchant le Mac de se mettre en veille.
# Usage : sh outils/nuit.sh              (toutes les histoires)
#         sh outils/nuit.sh --histoire H1 H2
# Journal : audio-genere/journal-AAAA-MM-JJ.txt
cd "$(dirname "$0")/.."
mkdir -p audio-genere
JOURNAL="audio-genere/journal-$(date +%Y-%m-%d).txt"
echo "Génération lancée. Journal : $JOURNAL  (tu peux fermer cette fenêtre en laissant le Mac allumé, pas le couvercle fermé)"
PYTORCH_ENABLE_MPS_FALLBACK=1 caffeinate -i "$HOME/omnivoice-env/bin/python" -u outils/generer_voix.py "$@" 2>&1 | tee -a "$JOURNAL"
