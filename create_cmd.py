# -*- coding: utf-8 -*-
"""
Script de création des lignes de commande pour appliquer des courbes à un ensemble d'images
"""
import argparse


def read_args():
    """Gestion des arguments"""

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="input data folder")
    parser.add_argument("-o", "--output", required=True, help="output data folder")
    parser.add_argument(
        "-c", "--curve", required=True, help="param file for images and curves"
    )
    parser.add_argument(
        "-a", "--acv", required=True, help="path of folder containing acv files"
    )
    parser.add_argument(
        "-f",
        "--file",
        required=False,
        help="output file containing command lines (cmd.txt)",
        default="cmd.txt",
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

for line in open(args.curve):
    fOut.write(
        "python apply_acv.py -i "
        + args.input
        + " -o "
        + args.output
        + " -a "
        + args.acv
        + " -c "
        + line
    )

fOut.close()
