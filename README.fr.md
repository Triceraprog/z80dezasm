# z80dezasm

z80dezasm est un outil conçu pour aider à désassembler et annoter des fichiers binaires Z80.
Le projet vise à comprendre d'anciennes ROM d'ordinateurs et à produire un fichier
en langage d'assembleur lisible par un humain, pouvant être réassemblé pour reformer le binaire original.

Consultez [l'historique](#historique-du-projet) du projet ci-dessous pour plus d'informations.

## Dépendances

### Pour le désassemblage et l'annotation :

- [Python 3.10](https://www.python.org/) or later ou version ultérieure
- [uv](https://docs.astral.sh/uv/)

### Pour la vérification *round-trip* :

- [sjasmplus](https://github.com/z00m128/sjasmplus) (doit être présent dans le PATH)
- Le paquet Python `watchdog` (pour le mode surveillance)

## Désassembleur

L'archive est fournie avec un fichier binaire de test.
Vous pouvez exécuter l'outil avec la commande suivante :

```
uv run z80dezasm --romfile example.rom --comments example.txt --crossref
```

Le résultat sera émis sur la sortie standard.


### Paramètres de commande

```
usage: z80dezasm [-h] --romfile ROMFILE [--crossref] --comments COMMENTS [--org ORG]
                 [--entry-point ENTRY_POINT]
```

- `romfile` est obligatoire et correspond au fichier binaire d'entrée que l'on souhaite désassembler.
- `comments` est obligatoire et correspond au fichier contenant les directives et commentaires qui aideront 
  à générer le résultat.
- `org` est l'origine du flux binaire (par défaut 0x0000). Il accepte toute valeur convertible en entier.
- `entry-point` est l'adresse de début du code du binaire (par défaut 0x0000). Il accepte toute valeur convertible en entier.

À propos de `entry-point` : son utilisation est principalement intéressante lorsque l'origine
n'est pas zéro, pour une ROM située ailleurs et atteinte par un mécanisme de saut.
Par exemple, pour le `Canon X-07`, le mécanisme de réinitialisation provoque un `jp $c3c3` qui est le point
d'entrée réel de la ROM.


### Assembleur généré

Le désassembleur suivra tous les chemins de code pour générer du code.
Les chemins de code par défaut sont le point d'entrée ($0000 par défaut) ainsi que toutes
les adresses de *restart* si l'origine est 0.
Des chemins de code supplémentaires peuvent être ajoutés via le fichier de commentaires.

Le désassembleur tentera également de détecter les chaînes de caractères.
Vous pouvez désactiver la détection pour une adresse ou une plage d'adresses dans le fichier de commentaires.

De plus, l'assembleur généré inclut :

- `OPT --syntax=a` pour pouvoir écrire des instructions comme `sub a,d` avec `sjasmplus`.
- `ORG $0000` pour définir l'origine (ou bien l'adresse spécifiée).
- Des définitions `EQU` pour les étiquettes pointant en dehors de la ROM.
- Des commentaires signalant tout nom d'étiquette entrant en conflit avec les mots-clés réservés
  de `sjasmplus` (`low`, `high`, `or`, etc.), lesquels sont remplacés par leur adresse numérique dans la sortie.


### Références croisées

Le paramètre `--crossref` ajoutera des commentaires sur les lignes qui sont appelées par un saut depuis d'autres adresses.

Pour les données d'exemple par exemple, avec `--crossref`, on obtient :

```asm
start:       ei                            ; $0083 fb              ; / appelé depuis : $0001
jump0084:    jp       jump0084             ; $0084 c3 84 00        ; / appelé depuis : $0084
```

Sans cette option, on obtient :

```asm
start:       ei                            ; $0083 fb              ; 
jump0084:    jp       jump0084             ; $0084 c3 84 00        ; 
```

Cela peut être utile lors de l'analyse, mais peut s'avérer encombrant lors de la publication.


## Format du fichier de commentaires

Le format du fichier de commentaires est décrit comme suit :

- Les 11 premières colonnes sont réservées à l'adresse ou à la plage d'adresses sur laquelle le commentaire s'applique.
- À partir de la colonne 13 sont placés les commentaires et les directives.
- Un nom entre crochets (`[` et `]`) est une étiquette (label), c'est-à-dire une adresse nommée.
  Elle est placée sur la même ligne que l'adresse ou la plage d'adresses.
- Le caractère `%` est un préfixe pour les balises, qui sont des directives :
    - `CODE` indique que cette adresse contient du code exécutable, même si aucun saut
      ou appel apparent n'y mène. Il est généralement utilisé avec des tables d'indirection ou des
      adresses calculées.
    - `SECTION` indique une nouvelle section. C'est ignorée par le désassembleur et sert
      davantage à l'organisation du fichier de commentaires.
    - `NTS` indique une « chaîne terminée par un zéro » (Null Terminated String) dans les données.
    - `MS_BASIC` indique une étiquette équivalente pour un BASIC de référence.
      Elle est ignorée et servait principalement d'aide lors de mes premières utilisations.
    - `CHAR` indique que le paramètre de l'opcode à cette adresse est un caractère.
      Le désassembleur remplacera la valeur numérique par le caractère correspondant.
    - `NOT\_LABEL` indique que le paramètre de l'opcode n'est pas une étiquette, même si la valeur
      correspond à une adresse d'étiquette valide.
    - `DATASKIP` indique que l'octet commenté n'est pas une instruction mais une donnée dans
      un chemin de code qui sera sauté par un mécanisme quelconque. L'exemple principal est la
      vérification d'un caractère spécifique dans un flux d'entrée où un `rst` est effectué,
      suivi du paramètre pour la routine, et la routine ajuste l'adresse de retour pour sauter le paramètre.
    - `NOSTRING` indique que cette partie ne doit pas être analysée comme une chaîne de caractères même
      si elle y ressemble. Par exemple, dans les tables de chaînes où le premier octet a son bit 7 à 1
      pour indiquer le début de la chaîne, le résultat de l'affichage des chaînes n'est pas très lisible.
      Je trouve préférable d'indiquer un `NOSTRING` : les données affichables sont de toute façon
      écrites dans les commentaires correspondants en sortie.
- Lorsqu'un commentaire est associé à une étiquette, il indique un commentaire général.
  Il est alors affiché avant l'étiquette dans la sortie.
- Lorsqu'un commentaire n'est pas associé à une étiquette, il indique un commentaire
  sur une ligne spécifique ou une plage. Il est alors affiché dans la partie commentaire
  des lignes, sur la droite.

## Vérification *round-trip*

`verify_roundtrip.py` désassemble une ROM, la réassemble avec `sjasmplus`,
puis compare le résultat avec l'original pour confirmer qu'ils sont identiques octet par octet.

C'est un moyen de vérifier que le résultat du désassemblage produit toujours l'entrée,
et donc que rien n'a été cassé par le système de désassemblage et de commentaires.

Le script a des paramètres similaires à ceux du désassembleur :

```
usage: verify_roundtrip.py [-h] --romfile ROMFILE --comments COMMENTS --output OUTPUT [--org ORG]
                           [--entry-point ENTRY_POINT] [--watch]
```

- `output` spécifie un nom de base qui sera utilisé pour créer les fichiers
  `output.asm` et `output.bin` contenant respectivement le fichier désassemblé et le binaire reconstruit.

**Mode batch** (exécution unique) :

```bash
> python3 verify_roundtrip.py --romfile example.rom --comments example.txt --output result
Writing assembly to result.asm
Assemble result.asm
Done assembly
Files are identical.
```

**Mode surveillance** (se réexécute automatiquement lorsque le fichier de commentaires change) :

```bash
python3 verify_roundtrip.py --romfile example.rom --comments example.txt --output result --watch
Writing assembly to result.asm
Assemble result.asm
Done assembly
Files are identical.
Watching xxxx for changes to example.txt...
```

Le mode surveillance est utile lors de l'analyse pour avoir une sorte de flux de travail
interactif où vos commentaires régénèrent le fichier de sortie au fur et à mesure de leurs modifications.

Il nécessite la dépendance optionnelle `watchdog` pour `python`.


## Exécution des tests

```bash
uv run pytest
```

## Historique du projet

Ce projet a été initialement lancé en 2017 sous la forme d'un ensemble de scripts pour désassembler
la ROM du Philips VG5000µ, un ordinateur personnel des années 1980, basé sur le Z80.

L'idée était de produire un fichier en assembleur commenté qui pourrait être réassemblé pour reformer
le binaire original. Ainsi, la ROM pouvait être comprise et documentée.
Elle pouvait également être modifiée. C'était avant tout un projet pour le fun.

Le désassemblage était basé sur cet [article]((http://z80.info/decoding.htm)) concernant le décodage des opcodes Z80.

Dès le début, je voulais avoir les commentaires dans un fichier dédié qui servirait de source
à injecter dans l'assembleur généré. De cette façon, les commentaires pouvaient être édités
et améliorés sans avoir à éditer et relire et retraiter le fichier assembleur généré.
Cela permet aussi de publier les commentaires sans avoir à fournir le fichier binaire.

Mon processus consistait à avoir un éditeur avec deux fenêtres : une pour éditer les commentaires
et l'autre pour lire la sortie. Un processus en arrière-plan surveillait les changements
dans le fichier de commentaires et relançait le désassemblage, vérifiant que le listing
généré pouvait être réassemblé pour reformer le binaire original.

C'est un peu plus lourd que d'annoter directement le fichier assembleur, mais cela aide si
je dois changer le formatage des commentaires (ce que j'ai fait quelques fois).

Une fonctionnalité dès le début était également de suivre le chemin du code à travers les instructions
`call` et `jp`, pour identifier rapidement les blocs de code des données, ainsi que l'annotation des
références croisées. J'ai aussi ajouté quelques commandes pour donner des indications
au désassembleur. Par exemple, marquer un bloc comme étant du code, ou spécifier qu'un
opcode apparent était en réalité des données.

J'ai plus tard utilisé l'outil pour vérifier certaines informations sur d'autres ordinateurs,
sans commentaire complet (PHC-25 et X07 par exemple).
