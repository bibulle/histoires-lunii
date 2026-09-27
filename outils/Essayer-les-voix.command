#!/bin/sh
cd "$(dirname "$0")/.."
PYTORCH_ENABLE_MPS_FALLBACK=1 "$HOME/omnivoice-env/bin/python" outils/generer_voix.py --essais
open "$HOME/Google Drive/Histoires Lunii – Les Aventures des Princesses/Audio (enregistrements)/0 – À trier (dépôt)/essais-omnivoice" 2>/dev/null
echo; echo "Tu peux fermer cette fenêtre."
