#!/bin/sh
# Installe OmniVoice sur le Mac (Apple Silicon, accélération GPU « mps »).
# Usage : sh outils/installer-omnivoice.sh      (à lancer une seule fois, dans Terminal)
set -e
ENV="$HOME/omnivoice-env"
cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "→ Installation de uv (gestionnaire Python)…"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "→ Environnement Python dans $ENV"
uv venv --python 3.11 "$ENV"
echo "→ Installation de PyTorch, OmniVoice…"
uv pip install --python "$ENV/bin/python" torch==2.8.0 torchaudio==2.8.0
uv pip install --python "$ENV/bin/python" omnivoice soundfile

echo "→ Téléchargement du modèle et test (quelques minutes la première fois)…"
PYTORCH_ENABLE_MPS_FALLBACK=1 "$ENV/bin/python" outils/generer_voix.py --essais --role PAILLETTE

echo ""
echo "✅ OmniVoice est installé. Écoute : audio-genere/_essais-voix/"
open audio-genere/_essais-voix 2>/dev/null || true
