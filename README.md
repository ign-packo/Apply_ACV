# Apply_ACV
Script d'application des courbes ACV

# Pré-requis

Le script utilse: gdal, numpy et scipy + pylint, flake8 pour la vérification du code pytyhon.
On peut créer un environnement conda avec la commande:
```
conda create --name apply_acv --file requirements.txt
```

# Utilisation

Trois paramètres:

- le nom du fichier texte au format SIA qui liste les courbes à appliquer par image
- le dossier qui contient les images à corriger
- le dossier de sortie des traitements (par défaut les images corrigées portent le même nom que les images en entrée)

Par exemple:
```
python apply_acv.py data/liste_reglages.txt data .
```

Il y a un script qui permet de comparer deux images (3 canaux 8 bits) et d'exporter une image des différences s'il y en a:

Par exemple:
```
python test_diff.py init.tif data/ref.tif
```

# Doc technique

L'ordre d'application des courbes dans le fichier texte est de droite à gauche. C'est-à-dire que sur l'exemple *data/liste_reglages.txt*, on applique:

1. IB_18.0.acv avec le masque IB_18.0.5.psb
2. bde5_2449_2455.0.acv sur le masque bde5_2449_2455.0.3.psb
3. bde5_2449_2455.1.acv sur le masque bde5_2449_2455.1.3.psb
4. bde5_2451_2453.0.acv sur le masque bde5_2451_2453.0.1.psb
5. bde5_2452.0.acv sur le masque bde5_2452.0.0.psb
6. Courbe_de_rehaussement.acv sans masque

Comme les fichiers PSB ne sont pas lisibles par GDAL on suppose qu'ils ont été transformé en TIF (on remplace l'extension).

Dans chaque fichier ACV, il y a 4 courbes:

0. une courbe qui s'applique sur les 3 canaux
1. une courbe pour le R
2. une courbe pour le V
3. une courbe pour le B

Il faut commencer par appliquer la courbe spécifique à chaque canal PUIS la courbe 0.

Pour interpoler les niveaux sur une courbe, il faut utiliser un spline comme condition limite la dérivée seconde à zéro:
```
# natural spline boundary conditions
order, value = ([(2, 0)],[(2, 0)])  
fct = make_interp_spline(courbe[::2], courbe[1::2], k=3, bc_type=(order, value)
```

Pour obtenir un résultat identifique à PhotoShop il faut faire attention aux arrondis, schématiquement:
````
Corr = Round(Masque/255 * Round(Lut(Init)) + (255-Masque)/255 * Init)
````

