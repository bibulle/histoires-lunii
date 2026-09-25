#!/bin/sh
# Régénère le livret et le publie sur GitHub Pages (branche gh-pages).
set -e
cd "$(dirname "$0")/.."
python3 livret/build.py
REMOTE=$(git remote get-url origin)
TMP=$(mktemp -d)
cp livret/site/index.html "$TMP/index.html"
touch "$TMP/.nojekyll"
cd "$TMP"
git init -q -b gh-pages
git add -A
git -c user.name="$(git -C "$OLDPWD" config user.name)" -c user.email="$(git -C "$OLDPWD" config user.email)" commit -qm "Livret du $(date +%d/%m/%Y)"
git -c credential.helper="$(git -C "$OLDPWD" config credential.helper)" push -qf "$REMOTE" gh-pages
cd "$OLDPWD" && rm -rf "$TMP"
echo "Publié sur la branche gh-pages"
