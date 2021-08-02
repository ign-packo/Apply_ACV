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
    parser.add_argument("-i", "--input", required=True, help="input image data folder")
    parser.add_argument("-o", "--output", required=True, help="output data folder")
    parser.add_argument(
        "-c", "--curve", required=True, help="param file for images and curves"
    )
    parser.add_argument(
        "-a", "--acv", required=True, help="path of folder containing acv files and masks"
    )
    parser.add_argument(
        "-f",
        "--file",
        required=False,
        help="output file containing command lines (cmd.txt)",
        default="cmd.txt",
    )
    parser.add_argument(
        "-b",
        "--blocksize",
        help="number of lines per block",
        default=1000
    )
    parser.add_argument(
        "-q",
        "--quality",
        help="JPEG Compression quality (100: No compression)",
        default=90
    )
    parser.add_argument(
        "-v", "--verbose", help="verbose (default: 0)", type=int, default=0
    )
    args = parser.parse_args()

    if args.verbose >= 1:
        print("\nArguments: ", args)

    return args


args = read_args()

fOut = open(args.file, "w")

cwd = os.getcwd()
pathApplyAcv = os.path.join(os.path.dirname(__file__), "apply_acv.py")

print(pathApplyAcv)

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

        fOut.write(
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
            + " -c "
            + line
        )
    else:  # pas de retouches a faire sur l'image
        compress = str()
        if int(args.quality) < 100:
            compress = " -co COMPRESS=JPEG -co QUALITY="+str(args.quality)
        else:
            compress = " -co COMPRESS=LZW"

        fOut.write(
            "gdal_translate"
            + " -of COG"
            + compress
            + " "
            + os.path.join(args.input, tile)
            + " "
            + os.path.join(args.output, tile)
            + "\n"
        )

fOut.close()
