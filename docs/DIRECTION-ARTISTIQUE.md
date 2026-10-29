# Direction artistique — listes MAL d'Orilo

## 1. Ce que font les meilleurs designs (étude du catalogue Shishio-kun, Theme Customiser, rl404)

| Design | Ce qui le rend fort |
|---|---|
| **Puni** (Valerio Lyndon) | Kit d'art complet **par onglet** : fond, bannière et 2-3 personnages détourés différents pour All / Current / Completed… Couleur d'accent qui change avec l'onglet. Motif de fond maison (pokéballs), icône de statut posée sur chaque cover, libellés de champ (Score, Episodes) façon fiche. |
| **Tilt** (Valerio Lyndon) | Le langage graphique de la série (MHA) appliqué à l'UI : navigation en blocs séparés par des slashs jaunes, logo sur mesure « 私のアニメリスト », personnage géant plein cadre derrière la liste. |
| **Brink** (Valerio Lyndon) | Affiches pleine hauteur, ruban « TOP RATED » or/argent/bronze selon la note, rang « #1 », flou + assombrissement de la cover au survol. |
| **Kure** | Illustration plein écran teintée, lignes translucides par-dessus, petit libellé manuscrit incliné (« Completed ») au-dessus de chaque ligne. |
| **Naruto / MHA / Haikyuu (Hahaido)** | Composition symétrique : deux personnages détourés qui **encadrent** la liste, logo de la série en titre. |
| **NieR Automata Menu** | Reproduction fidèle d'une UI de jeu (papier beige, typographie de menu) : la liste devient un écran du jeu. |

Constat sur mes premiers jets : UI générique (dégradés, pastilles, glow) posée sur la même structure que Clarity, **aucun univers, aucune illustration, aucun détail propre à une œuvre**. C'est exactement ce que les bons designs évitent.

### Principes retenus
1. **Un univers, pas une palette.** Chaque thème part d'une œuvre précise et en reprend le langage visuel (objets, symboles, typographie, vocabulaire).
2. **L'art est le héros, l'UI s'y insère.** Illustration principale + personnages détourés qui débordent du cadre ; la liste est un élément de la composition (panneau, cadre, écran), pas des cartes flottantes.
3. **Par onglet de statut, un décor.** `body[data-query*='"status":N']` (7 All, 1 En cours, 2 Terminés, 3 En pause, 4 Abandonnés, 6 Prévus) change fond, bannière, personnages, accent et textes.
4. **Les détails font le design** : icônes de statut sur les covers, rubans de note, notes traduites dans l'univers (chiffres romains, tubes nixie, fleurs…), survols signifiants, popups de filtres, spinner, barre collante, pied de page, outils du propriétaire, tous thématisés.
5. **Retenue typographique** : deux polices maximum, dont une qui « parle » l'œuvre.

## 2. Boîte à outils technique

- **Onglet courant** : `body[data-query*='"status":2'] { --bg-art: url(...); }`.
- **Personnages détourés** : plusieurs couches dans une seule variable, positionnées et dimensionnées :
  `--renders: url(a.png) calc(50% - 520px) 100% / auto 520px no-repeat, url(b.png) calc(50% + 540px) 100% / auto 480px no-repeat;`
- **Note → visuel** : la note n'existe que sous forme de classe (`.score-label.score-8`). Chaque classe peut donner un contenu (`content: "VIII"`), une largeur de jauge (`width: calc(8 * 14px)` sur un fond répété), une couleur, un ruban. `:has(.score-10)` permet de styler toute la ligne.
- **Icône de statut sur la cover** : `.data.watching ~ .data.image a::before`.
- **Covers HD** : `@\import "https://cover.mal.rl404.com/Orilo/anime?style=..."` (service rl404, testé OK).
- **Structure** : `tbody.list-item > tr.list-table-data > td.data.{status,number,image,title,score,type,progress}` ; manga : `td.data.chapter` / `td.data.volume` (singulier) ; le bouton « All » garde la classe `all_anime` sur la liste manga.
- **Visiteur vs propriétaire** : `.header-menu.other` (visiteur) ; `[data-owner="1"]`, `.list-menu-float`, `.add-edit-more`, notes/score/progression éditables, `tr.more-info` (propriétaire).

### Contraintes MAL
- `@import` n'est servi qu'au propriétaire : écrire `@\import "..."` (forme chaîne). Google Fonts via l'API v1 (`css?family=A:400,700|B`), sans `;` ni `@` dans l'URL.
- `url()` uniquement vers des `.jpg`, `.png`, `.gif` (MAL les relaie via son proxy). Pas de SVG ni de `data:`.
- Le non-ASCII est corrompu au rendu : tout caractère spécial dans `content` en échappement CSS (`"\2605"`).

### Assets
- **Créés pour le projet** (PNG/GIF générés, originaux) : `themes/<thème>/assets/`, publiés via jsDelivr :
  `https://cdn.jsdelivr.net/gh/pmharquet/mal-style-css@main/themes/<thème>/assets/<fichier>.png` (dépôt à pousser sur GitHub).
- **Illustrations de l'œuvre** (wallpapers, personnages détourés) : liens directs `.jpg`/`.png` regroupés dans la section CONFIG de chaque thème, remplaçables.

## 3. Thèmes

### DIVERGENCE — Steins;Gate
Le laboratoire des Future Gadgets. Héros : un **compteur de divergence** en tubes nixie (verre, grille, chiffres orange incandescents) au-dessus d'une illustration sombre du labo. Chaque onglet affiche une ligne d'univers différente (All 1.048596 · En cours 0.571024 · Terminés 1.130205 · En pause 0.337187 · Abandonnés 0.000000 · Prévus 1.382733). Liste façon terminal CRT ambre/phosphore : numéro « LAB MEM 012 », note dans **un tube nixie** par ligne, progression en chiffres de terminal, scanlines et aberration chromatique sur les covers au survol. Onglets = commandes de terminal. Pied de page « El Psy Kongroo. ».

### ZERO REQUIEM — Code Geass
Noir, violet impérial, rouge Geass, or britannien. Zero / Lelouch en grand à gauche, cape qui traverse la page ; **sigil du Geass** rouge pulsant derrière l'avatar. Motif échiquier en perspective ; onglets = pièces d'échecs (♚ ♞ ♛ ♜ ♟ ♝). Liste = registre des Chevaliers Noirs, filets dorés ; 10/10 = ruban « CHECKMATE ». Survol : un sigil Geass s'allume sur la cover. Personnage différent par onglet (Lelouch, C.C., Suzaku, Kallen…).

### JOURNEY'S END — Sousou no Frieren
Thème clair. Paysage aquarelle qui se fond dans un papier vergé ; **cercle magique doré** multi-anneaux qui tourne lentement derrière l'avatar, particules de lumière. Onglets = étapes sur un chemin de carte en pointillés. Liste = carnet de voyage : filets dorés, covers montées comme des photos collées, note = **fleurs bleues** (jauge de fleurs selon la note). Saison différente par onglet (printemps en cours, automne doré pour les terminés, hiver en pause…).

### BANKAI — Bleach : Thousand-Year Blood War
Noir et blanc tranché, rouge sang. Composition cinéma : immense kanji vertical 卍解, éclaboussures d'encre, Ichigo en monochrome. Covers en noir et blanc qui reprennent leur couleur au survol, avec une **entaille rouge** qui traverse la ligne. Onglets = divisions du Gotei 13 en chiffres kanji. Titres de section façon cartons d'épisode de TYBW.

### NAZARICK — Overlord
Salle du trône du Grand Tombeau : obsidienne, pourpre, or. Ainz sur son trône au centre de la bannière, cadres gothiques dorés. Liste = registre des Gardiens d'étage : plaques gravées, gemme de statut, note en **chiffres romains**. Chaque onglet = un étage, avec son gardien (Albedo, Shalltear, Demiurge, Cocytus, Aura & Mare).
