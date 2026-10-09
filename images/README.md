# Images du pack

Les 35 images de l'écran de la Lunii, une par segment qui en a besoin. Le nom du fichier est le code du segment.

| Fichiers | Écran |
|---|---|
| `Menu0-accueil` | le château des Princesses |
| `Menu1-Romy`, `Menu1-Alix`, `Menu1-Romy&Alix` | qui part à l'aventure |
| `Menu2-H1` … `Menu2-H9` | le titre de chaque histoire |
| `Menu3-Paillette`, `-Grumo`, `-TataBetise`, `-Papic`, `-Mamily` | le compagnon |
| `H1-5a`, `H1-5b` … `H8-4a`, `H8-4b` | les deux réponses du choix de chaque histoire |
| `Fin-autre-aventure` | encore une aventure ? |

- `png/` : les images à donner à STUdio (320×240, fond noir, 16 couleurs au plus).
- `svg/` : les mêmes dessins en vectoriel.
- `planche.png` : toutes les images sur une page, pour relire.

## Règles de dessin
- **320×240, fond noir** : le noir est l'écran éteint, le dessin semble flotter derrière la coque.
- **16 couleurs au plus par image, en aplats** : pour les Lunii à firmware v2 et plus, STUdio réduit chaque image à 16 couleurs avec un tramage qui ternit tout. Les PNG sont donc déjà réduits proprement, sans dégradé ni transparence.
- **Gros et simple** : un sujet par image, pas de détail plus fin que 4 pixels.
- Romy : couettes, barrette dorée, robe à carreaux bleus, tour rose du château. Alix : cheveux blonds lâchés, robe rose, tour bleue.

## Refaire les images
Les dessins sont écrits en Python : `dessins.py` (les personnages), `scenes.py` (accueil, titres, choix, fin), `rendu.py` (fabrique `svg/`, `png/` et `planche.png`).

```
pip install playwright pillow numpy && playwright install chromium
python3 images/rendu.py
```
