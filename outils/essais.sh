#!/bin/sh
# Génère une phrase test pour chaque voix de Sources qui n'a pas encore d'essai.
# Pour refaire l'essai d'une voix : supprime (ou renomme) son fichier Essai_… dans le Drive.
# Usage : sh outils/essais.sh
cd "$(dirname "$0")/.."
PYTORCH_ENABLE_MPS_FALLBACK=1 "$HOME/omnivoice-env/bin/python" -u outils/generer_voix.py --essais "$@"
open "$HOME/Google Drive/Histoires Lunii – Les Aventures des Princesses/Audio (enregistrements)/0 – À trier (dépôt)/essais-omnivoice" 2>/dev/null
