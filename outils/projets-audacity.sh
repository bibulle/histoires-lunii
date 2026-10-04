#!/bin/sh
# Crée un projet Audacity par segment (sans toucher aux projets existants).
# Avant : ouvrir Audacity 3.7 avec mod-script-pipe activé (Préférences › Modules).
# Usage : sh outils/projets-audacity.sh --liste     (voir ce qui sera créé)
#         sh outils/projets-audacity.sh             (tout créer)
#         sh outils/projets-audacity.sh --histoire H2 Menus
#         sh outils/projets-audacity.sh --perimes   (montages .wav plus vieux que les prises ou
#                                                    les morceaux qu'ils contiennent ; Audacity pas nécessaire)
cd "$(dirname "$0")/.."
exec "$HOME/omnivoice-env/bin/python" -u outils/creer_projets_audacity.py "$@"
