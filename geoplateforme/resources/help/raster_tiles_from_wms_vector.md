- Description :

Création de tuiles raster depuis un service WMS-VECTOR.

- Paramètres :

| Entrée           | Paramètre          | Description                                                |
|------------------|--------------------|------------------------------------------------------------|
| Identifiant de l'entrepôt    | `DATASTORE`        | Identifiant de l'entrepôt utilisé pour la création de la livraison.  |
| Nom des tuiles raster | `STORED_DATA_NAME`      | Nom des tuiles raster. |
| Nom des couches à moissonner | `HARVEST_LAYERS`      | Nom des couches à moissonner. Valeurs multiples séparées par des virgules.|
| Niveaux de moissonage| `HARVEST_LEVELS`      | Niveaux de moissonage. Valeurs multiples séparées par des virgules. |
| Paramètres de requêtes GetMap additionnels. | `HARVEST_EXTRA`      | Paramètres de requêtes GetMap additionnels. |
| Format des images téléchargées. | `HARVEST_FORMAT`      | Format des images téléchargées (défaut image/jpeg). |
| URL du service WMS | `HARVEST_URL`      | URL du service WMS. |
| Zone moissonnage | `HARVEST_AREA`      | Zone moissonnage |
| Le niveau du bas de la pyramide en sortie | `BOTTOM`      | Le niveau du bas de la pyramide en sortie. |
| Le niveau du haut de la pyramide en sortie | `TOP`      | Le niveau du haut de la pyramide en sortie. |
| Compression des données en sortie | `COMPRESSION`      | Compression des données en sortie. Valeurs possibles : "jpg", "png", "none", "png", "zip", "jpg90" |
| Le nombre de tuile par dalle en hauteur | `HEIGHT`      | Le nombre de tuile par dalle en hauteur (défaut : 16)|
| Le nombre de tuile par dalle en largeur | `WIDTH`      | Le nombre de tuile par dalle en largeur (défaut : 16) |
| Identifiant du quadrillage à utiliser (Tile Matrix Set) | `TMS`      | Identifiant du quadrillage à utiliser (Tile Matrix Set). Défaut : PM |
| Format des canaux dans les dalles en sortie | `SAMPLE_FORMAT`      | Format des canaux dans les dalles en sortie. Valeurs possible : "UINT8", "FLOAT32" |
| Nombre de canaux dans les dalles en sortie | `SAMPLES_PER_PIXEL`      | Nombre de canaux dans les dalles en sortie. Valeur entre 1 et 4, défaut : 3 |
| Nombre de thread pour la parallelisation | `PARALLELIZATION`      | Nombre de thread pour la parallelisation. Valeur entre 1 et 8, défaut : 4 |
| Attendre la fin de la génération  ? | `WAIT_FOR_GENERATION` | Option pour attendre la fin de la génération avant de sortir du traitement, permet de vérifier si les tuiles raster ont été correctement générées. (Désactivée par défaut) |
| Tags à ajouter | `TAGS`  | List de tags à importer. Format `"clé 1,valeur 1;clé 2,valeur 2;..;clé n,valeur n"` |

- Sorties :

| Sortie                             | Paramètre                           | Description                    |
|------------------------------------|-------------------------------------|--------------------------------|
| Identifiant de la tuile raster créée | `CREATED_STORED_DATA_ID`        | Identifiant de la tuile raster créée  |
| Identifiant de l'exécution du traitement | `PROCESSING_EXEC_ID`        | Identifiant de l'exécution du traitement  |

Nom du traitement : `geoplateforme:raster_tiles_from_wms_vector`
