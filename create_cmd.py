# -*- coding: utf-8 -*-
"""
Script de création des lignes de commande pour appliquer des courbes à un ensemble d'images
"""
import argparse
import os
import glob


def read_args():
    """Gestion des arguments"""

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="input image data folder path")
    parser.add_argument("-o", "--output", required=True, help="output data folder path")
    parser.add_argument(
        "-c", "--curve", required=True, help="param file for images and curves"
    )
    parser.add_argument(
        "-a", "--acv", required=True, help="folder path containing acv files and masks"
    )
    parser.add_argument(
        "-f",
        "--file",
        required=False,
        help="output file path containing command lines (default: ./cmd.txt)",
        default="cmd.txt",
    )
    parser.add_argument(
        "-b",
        "--blocksize",
        help="number of lines per block (default: 1000)",
        default=1000
    )
    parser.add_argument(
        "-p",
        "--projection",
        help="EPSG code for output files projection (if needed)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        help="JPEG compression quality (default: 90)",
        default=90
    )
    parser.add_argument(
        "-v", "--verbose", help="verbose (default: 0)", type=int, default=0
    )
    args_cmd = parser.parse_args()

    if args_cmd.verbose >= 1:
        print("\nArguments: ", args_cmd)

    return args_cmd


args = read_args()

# verification de la validite de la projection demandee
if args.projection:
    if not args.projection.isdigit() or len(args.projection) < 4 or len(args.projection) > 5:
        raise SystemExit('** ERREUR: '
                         'La projection indiquee n\'est pas valable ! '
                         + args.projection)

# verification validite pour quality
if args.quality not in range(0, 101):
    raise SystemExit('** ERREUR: '
                     "La valeur choisie pour 'quality' est invalide ! "
                     + str(args.quality))

fOut = open(args.file, "w")

cwd = os.getcwd()
pathApplyAcv = os.path.join(os.path.dirname(__file__), "apply_acv.py")

listFiles = glob.glob(os.path.join(args.input, '*.tif'))

f = open(args.curve, 'r')

listCurves = []
listCmd = []

for line in f:
    listCmd.append(line)
    listCurves.append(line.split(',')[0])


for file in listFiles:
    tile = os.path.basename(file)

    if tile in listCurves:  # on fait des retouches sur l'image
        index = listCurves.index(tile)
        line = listCmd[index]

        if not line.endswith('\n'):
            line = line + '\n'

        cmd_apply_acv = (
            "python "
            + pathApplyAcv
            + " -i "
            + args.input
            + " -o "
            + args.output
            + " -a "
            + args.acv
            + " -b "
            + str(args.blocksize)
            + " -q "
            + str(args.quality)
            + " -p "
            + args.projection
            + " -c "
            + line
        )

        fOut.write(cmd_apply_acv)
    else:  # pas de retouches a faire sur l'image
        if int(args.quality) < 100:
            gdal_param = " -co COMPRESS=JPEG -co QUALITY="+str(args.quality) + " "
        else:
            gdal_param = " -co COMPRESS=LZW "

        if args.projection:
            gdal_param = "-a_srs EPSG:"+args.projection+" "

        fOut.write(
            "gdal_translate"
            + " -of COG -co BIGTIFF=YES "
            + gdal_param
            + os.path.join(args.input, tile)
            + " "
            + os.path.join(args.output, tile)
            + "\n"
        )

fOut.close()
