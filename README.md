# Styles pour les listes MyAnimeList d'Orilo

Cinq thèmes complets pour le template **Modern** de MAL ([anime](https://myanimelist.net/animelist/Orilo), [manga](https://myanimelist.net/mangalist/Orilo)).
Chacun est construit autour d'une œuvre de tes favoris, avec un décor différent par onglet de statut.
La démarche et l'étude des designs de référence sont dans [docs/DIRECTION-ARTISTIQUE.md](docs/DIRECTION-ARTISTIQUE.md).

| Thème | Œuvre | En deux mots |
|---|---|---|
| [DIVERGENCE](themes/divergence/) | Steins;Gate | Compteur de divergence en tubes nixie animés, liste dans un moniteur CRT, note de chaque ligne dans un tube. |
| [ZERO REQUIEM](themes/zero-requiem/) | Code Geass | Héros plein écran par onglet, onglets en rangée d'échiquier, registre des Chevaliers Noirs, sigil du Geass au survol. |
| [JOURNEY'S END](themes/journeys-end/) | Sousou no Frieren | Thème clair : carnet de voyage aquarelle, cercle magique doré, itinéraire de carte, note en fleurs bleues. |
| [BANKAI](themes/bankai/) | Bleach TYBW | Encre sur papier washi, kanji au pinceau, onglets = étapes de libération du sabre, coup de pinceau rouge au survol. |
| [NAZARICK](themes/nazarick/) | Overlord | Salle du trône du Grand Tombeau, plaques dorées, note en chiffres romains, un étage et son gardien par onglet. |

Les aperçus sont dans chaque dossier (`preview-*.jpg`).

## Installation

1. **Publier les images générées** (une seule fois) : les thèmes chargent leurs assets depuis
   `https://cdn.jsdelivr.net/gh/pmharquet/mal-style-css@main/…`. Le dépôt doit donc être poussé sur GitHub
   (`pmharquet/mal-style-css`, public). Sans ça, le thème s'affiche mais sans ses éléments graphiques maison.
2. Sur https://myanimelist.net/ownlist/style : template **Modern**, thème **Default Theme** pour l'anime et le manga, **Save**.
3. Cliquer sur le thème → **Add Custom CSS** → coller tout le contenu de `themes/<thème>/theme.css` → **Save**.
4. Colonnes conseillées (Anime List Settings) : Numbers, Image, Score, Type, Progress. Manga : Numbers, Image, Score, Chapters, Volumes.

Écrans pris en charge : de 768 px (tablette) jusqu'aux écrans ultra-larges 21:9, où la composition reste dans une scène centrée.
En dessous, inutile : MAL sert son site mobile, sans CSS personnalisé, aux téléphones.

Personnalisation : uniquement la section `CONFIG` en haut de chaque fichier (illustrations par onglet, avatar, textes).
MAL n'accepte que des images `.jpg`, `.png` ou `.gif`.

## Structure

```
themes/<thème>/theme.css        CSS à coller dans MAL
themes/<thème>/assets/          images originales générées (publiées via jsDelivr)
themes/<thème>/src/             script Python qui régénère les assets
docs/DIRECTION-ARTISTIQUE.md    étude des designs de référence + directions artistiques
backup/                         ton CSS actuel (Clarity modifié), sauvegardé avant tout changement
archive/premiers-jets/          premières propositions, abandonnées
tools/check_theme.py            vérifie les contraintes MAL (imports, url, non-ASCII, assets présents)
tools/preview/                  banc d'essai local (copie de tes listes) + captures headless
```

## Banc d'essai local

```bash
python tools/preview/build.py Orilo
```

```bash
python -m http.server 8765
```

```bash
node tools/preview/shot.mjs divergence --status 2 --hover 3 --scroll 600
```

`build.py` télécharge tes listes publiques (anime, manga, et une variante « propriétaire » avec le menu flottant et les contrôles d'édition).
`shot.mjs` produit une capture dans `tools/preview/shots/` (options : `--list anime|manga|owner-anime|owner-manga`, `--status 7|1|2|3|4|6`, `--hover N`, `--scroll Y`, `--width W`, `--full`).
Dépendance : `npm install` dans `tools/preview/` (puppeteer-core, utilise le Chrome installé).
`sh tools/preview/make_previews.sh <thème>` régénère les `preview-*.jpg` d'un thème ; `python tools/check_theme.py themes/*/theme.css` vérifie les contraintes MAL.

## Contraintes MAL à connaître

- `@import` n'est servi qu'au propriétaire de la liste : écrire `@\import "…"` pour que les visiteurs l'aient aussi.
- `url()` uniquement vers `.jpg` / `.png` / `.gif` ; MAL les relaie via son proxy d'images.
- Les caractères non-ASCII sont corrompus au rendu : dans `content`, utiliser des échappements CSS (`"\2605"`).
- L'onglet courant se lit avec `body[data-query*='"status":N']` (7 All, 1 En cours, 2 Terminés, 3 En pause, 4 Abandonnés, 6 Prévus).
