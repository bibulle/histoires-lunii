# Personnages et voix

**Règle d'écriture** : chaque personnage a une signature, mais ses répliques changent d'une histoire à l'autre. Sa formule fétiche n'apparaît qu'une ou deux fois dans toute la série.

| Personnage | Caractère | Voix |
|---|---|---|
| Narrateur | Le conteur | Calme et chaleureuse (Papic ou Mamily en « voix de conteur ») |
| Princesse Romy | La grande (3 ans), très fière d'aller à l'école, montre l'exemple | Claire, un peu solennelle |
| Princesse Alix | Garçon manqué (2 ans), fonce toujours | Pétillante, rapide |
| Prince Mathéo | Le bébé prince (6 mois), ses bruits de bébé déclenchent la magie | Gazouillis, rires (idéalement ses vrais enregistrements) |
| Papic | Le grand inventeur du château, bricole dans son atelier | Grave, bourru mais tendre + bruits d'outils |
| Mamily | Reine des câlins et des gâteaux, gâte tout le monde | Douce et chantante |
| Tata Bêtise | Gentille catastrophe ambulante, assume ses bêtises en riant | Aiguë, rigolote, toujours un éclat de rire |
| Paillette la licorne | Un peu timide, chante quand elle est contente | Fluette, notes de clochette |
| Grumo le dragon | Gros, gentil, enrhumé : éternue des bulles au lieu du feu | Caverneuse |

## Réserve de répliques (à varier)

**Romy** : « Je suis une grande, moi ! » (signature, H1 seulement) · « Moi je sais ! » · « Regarde, je te montre ! » · « Fais comme moi ! » · « J'ai une idée ! » · « Écoute bien… »

**Alix** : « Vite, vite ! » · « Suivez-moi ! » · « Moi d'abord ! » · « Même pas peur ! » · « Hop, j'y vais ! » · « Un, deux, trois… partez ! » · « On recommence ? »

**Mathéo** : « Areuh ! » · « Ba-ba-ba ! » · « Gueu-gueu ! » · « Aaah ! » · éclats de rire · applaudissements [clap clap] · « Mmmh… » (endormi)

**Papic** : « Hmm hmm, voyons voir… » (signature, 2 fois max) · « Pas de problème ! » · « Laisse faire Papic ! » · « J'ai l'outil qu'il faut ! » · « Un petit coup de tournevis, et hop ! » · « Heureusement que je suis là ! »

**Mamily** : « Mes caillettes ! » (signature, H1 et H9) · « Mes petites puces ! » · « Mes cocottes ! » · « Oh, mes amours ! » · « Mes chéries ! »

**Tata Bêtise** (jamais « c'est pas moi », toujours le mot « bêtise » et un rire) : « Oups ! Encore une bêtise ! Hi hi hi ! » · « Oups-la-boum ! Une toute petite bêtise… » · « Oh là là, encore une bêtise ! Ha ha ha ! » · « Oh la boulette ! Pas grave, on répare ! » · « Ça, c'est une bêtise de Tata Bêtise ! » · « J'ai fait une bêtise mouillée ! » · « Celle-là, c'est la plus rigolote de mes bêtises ! »
Les autres lui répondent en riant, jamais en la grondant, et pas toujours avec la même phrase.

**Paillette** : chante, mais pas toujours la même chose : « La la laaa ! » · « Tra-la-li-laaa ! » · petite chanson de rangement · chanson de Noël « Ding, ding, dong… » · « Comme c'est joli ! »

**Grumo** : l'éternuement change à chaque fois : « ATCHOUM ! » · « Aaah… TCHOUM ! » · « A-a-atchi ! » · « Aaaa… TCHA ! » · « Atchoum-boum ! » · « ATCHOUUUUM ! »

## Personnages secondaires (une seule histoire)
- Le Père Noël (H8) : voix grave, « Ho ho ho ! »
- Tornade, le petit renne (H8) : pas de voix, bruits de clochettes
- Pipou le bébé dauphin et sa maman (H6) : voix aiguës, rires « i-hi-hi »
- Noisette l'écureuil (H7) : petite voix douce
- Le crabe et le poisson rouge (H6) : petites voix rigolotes

Romy et Alix sont très complices : dans les versions « les deux princesses », elles s'entraident (Romy montre, Alix fonce).

## Idées pour les voix
- Répartir les rôles en famille : Papic = Bibulle, Mamily = la vraie Mamily, Tata Bêtise = la vraie tata si possible.
- **Mathéo** : demander à ses parents d'enregistrer ses vrais gazouillis et éclats de rire au téléphone. Ce sera magique pour les filles.
- Les princesses : les voix peuvent être jouées par un adulte. Autre idée : glisser une ou deux vraies phrases de Romy et d'Alix enregistrées discrètement.

## Générer les voix avec OmniVoice

Dans les scripts, les **balises en anglais** placées dans les répliques (`[laughter]`, `[sigh]`…) sont des balises OmniVoice (modèle officiel `k2-fsa/OmniVoice`). Les **bruitages en français** (`[bulles]`, `[clochette]`…) sont à ajouter dans Audacity : ne jamais les coller dans OmniVoice.

**Mode d'emploi** : copier le texte entre « » (balises comprises) dans OmniVoice, langue *French*. Pour les voix jouées par la famille, la balise sert simplement d'indication de jeu.

| Balise | Effet | Utilisée pour |
|---|---|---|
| `[laughter]` | un rire | Tata Bêtise, les rires de Grumo, Papic, Mamily, le Père Noël… |
| `[sigh]` | un soupir | Paillette qui a peur, Grumo triste, Pipou, Noisette |
| `[surprise-oh]` / `[surprise-ah]` / `[surprise-wa]` | un « oh ! », « ah ! », « wa ! » étonné | émerveillement, Grumo qui vole |
| `[dissatisfaction-hnn]` | un « hmm » pas content | Romy qui mène l'enquête (H5) |

Autres balises existantes, pas utilisées pour l'instant : `[question-ah]`, `[question-oh]`, `[question-en]`, `[question-ei]`, `[question-yi]`, `[surprise-yo]`, `[confirmation-en]`. Il n'y a **pas** de balise pour renifler ou éternuer : « Snif » et « ATCHOUM » restent écrits en toutes lettres, ou se font en bruitage.

**Astuces**
- Si « Hi hi hi » ou « Ha ha ha » est lu comme des mots au lieu d'être ri, supprimer ces mots dans OmniVoice et garder seulement `[laughter]`.
- Si une phrase est coupée : générer une petite phrase à la fois, remplacer les « … » par des points, ou ralentir (vitesse 0,9).
- Pas d'émotion « peur » dans OmniVoice : pour Paillette, jouer sur le `[sigh]`, les silences dans Audacity et un léger trémolo (sinus, 40-60 %, 6-8 Hz).
- Une fois une voix réussie, garder le clip (5 à 10 s) et s'en servir comme référence (clonage) pour toutes les répliques du personnage, dans les 9 histoires.

**Voix de départ (mode « conception de voix », champ *instruct*)**. OmniVoice a appris ces voix sur de l'anglais et du chinois : en français le résultat varie, il faut parfois générer plusieurs fois.

| Personnage | instruct |
|---|---|
| Narrateur (si pas de voix famille) | `male, middle-aged, low pitch` |
| Romy | `female, child, moderate pitch` |
| Alix | `female, child, high pitch` |
| Paillette | `female, child, very high pitch` (+ `whisper` dans H9) |
| Grumo | `male, middle-aged, very low pitch` |
| Tata Bêtise (maquette) | `female, young adult, high pitch` |
| Papic / Mamily (maquette) | `male, elderly, low pitch` / `female, elderly, moderate pitch` |
| Père Noël | `male, elderly, very low pitch` |
| Pipou / Maman dauphin | `male, child, very high pitch` / `female, middle-aged, high pitch` |
| Noisette | `female, teenager, high pitch, whisper` |
| Le crabe / Le poisson rouge | `male, middle-aged, high pitch` / `male, child, moderate pitch` |
