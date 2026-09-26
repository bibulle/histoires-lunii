# Histoires Lunii – Plan du projet

Cadeau de Noël 2026 : des histoires personnalisées dans la Lunii de Romy (3 ans) et Alix (2 ans), avec leur cousin Mathéo (6 mois).
Nom du pack proposé : **« Les Aventures des Princesses »**

## Principes (adaptés à 2-3 ans)
- Histoires courtes : 3 à 4 minutes par parcours.
- Peu de choix, très clairs (les parents tourneront la molette au début).
- Répétitions, petites formules et bruitages qui reviennent, mais des répliques variées d'une histoire à l'autre.
- Aucune peur : pas de méchant, juste des petits problèmes doux.
- Fins rassurantes (câlin, goûter, bonne nuit).
- Plusieurs voix différentes (elles adorent).

## Structure dans la Lunii (3 niveaux de menu + 1 choix dans l'histoire)

```
Accueil
 └─ Menu 1 : Qui part à l'aventure ?  → Romy / Alix / Les deux princesses
     └─ Menu 2 : Quelle histoire ?    → 9 titres
         └─ Menu 3 : Qui vient avec toi ? → 3 compagnons (selon l'histoire)
             └─ Histoire
                 ├─ Début
                 ├─ CHOIX au milieu → Branche A ou Branche B
                 ├─ Les branches se rejoignent (principe du « losange »)
                 └─ Fin → « Tu veux une autre aventure ? » → retour Menu 2
```

- Compagnons par défaut : Paillette la licorne, Grumo le dragon, Tata Bêtise. Quand l'un d'eux est la vedette de l'histoire, il est remplacé par Papic ou Mamily.
- L'histoire du dodo (n°9) n'a ni menu compagnon ni choix, pour rester calme.

### Conventions des scripts
- **[×3]** : segment enregistré 3 fois (version Romy / Alix / les deux). Pour « les deux », accorder au pluriel en lisant.
- **[×compagnon]** : une version par compagnon.
- **[commun]** : enregistré une seule fois.
- Les segments [commun] et [×compagnon] ne nomment jamais la princesse, pour pouvoir être réutilisés partout.
- Bruitages entre crochets : [boing], [clochette]…
- Chaque segment a un code (ex. `H2-5a`) qui servira de nom de fichier MP3.

### Point technique important
La Lunii n'a pas de « mémoire » : pour qu'une fin dise « Romy » après un choix, le graphe doit garder des chemins séparés par héroïne et compagnon (3 × 3 = 9 chemins par histoire). Les **fichiers audio sont réutilisés** dans ces chemins : on n'enregistre pas plus, c'est seulement le graphe STUdio qui est plus gros.
Idée : comme les scripts sont codés, on pourra **générer le pack automatiquement** (story.json STUdio) avec un petit script Python au lieu de tout cliquer à la main.

## Le château
Le château est **rose pour Romy**, **bleu pour Alix** et **rose et bleu** quand les deux princesses partent ensemble. La couleur n'est dite que dans les segments [×3] ; les segments communs parlent du « château des princesses ».

## Narrateur
Papic et Mamily racontent à tour de rôle : Papic pour H1, H4, H7, H9 ; Mamily pour H2, H3, H5, H6, H8. Les menus de la Lunii sont dits à deux voix.

## Textes des menus (communs)
- **Accueil** : « Bienvenue au château des Princesses ! Tourne la molette pour choisir, et appuie sur le bouton pour commencer ! »
- **Menu 1** : « Qui part à l'aventure aujourd'hui ? »
  - « La Princesse Romy ! » / « La Princesse Alix ! » / « Les deux princesses, ensemble ! »
- **Menu 2** : « Quelle histoire veux-tu écouter ? » + le titre lu pour chaque histoire.
- **Menu 3** : « Qui vient avec toi ? »
  - « Paillette, la licorne ! [clochette] » / « Grumo, le dragon ! [ATCHOUM] » / « Tata Bêtise ! [Oups !] » / « Papic ! [marteau] » / « Mamily ! [bisou] »
- **Choix dans l'histoire** : la question se termine toujours par « Tourne la molette pour choisir ! »
- **Fin** : « Tu veux une autre aventure ? Tourne la molette ! »

## Chaîne technique
- STUdio : éditeur de packs (open source), construit le graphe images + audios.
- Lunii.QT : transfert des packs sur la Lunii.
- Images : 320×240, simples et lisibles (une par personnage, histoire, choix).
- Audio : MP3, montage et musique avec Audacity.
- À vérifier d'abord : modèle et firmware de la Lunii (les modèles récents sont plus contraignants).

## Où sont les fichiers
- **Textes** : ce dépôt GitHub (source de référence), avec une copie locale dans `Documents/histoires-lunii` sur le Mac.
- **Livret famille** : page web générée depuis ce dépôt, partagée avec Mamily et Tata.
- **Audio et images** : dossier Google Drive « Histoires Lunii – Les Aventures des Princesses ».

## Planning (fin septembre → Noël)
| Semaines | Étape |
|---|---|
| 1-2 | Valider la chaîne technique avec un pack test (1 image + 1 son) |
| 2-4 | Valider et ajuster les 9 scripts |
| 4-7 | Répéter, préparer les voix et bruitages |
| 7-9 | Enregistrer les voix (famille : Papic, Mamily, Tata Bêtise…) |
| 8-10 | Illustrations |
| 10-11 | Assemblage (ou génération) du pack + test de tous les parcours |
| 12 | Marge de sécurité, emballage |

## Avancement
- [x] Plan général
- [x] Personnages et voix définis
- [x] Structure 3 menus + choix dans l'histoire
- [x] Premier jet des 9 scripts
- [x] Tata Bêtise positive, répliques variées
- [ ] Valider les scripts (voir la liste « À valider » dans 03-sommaire.md)
- [ ] Vérifier modèle / firmware de la Lunii
- [ ] Pack test
- [ ] Enregistrements
- [ ] Illustrations
- [ ] Assemblage et tests
