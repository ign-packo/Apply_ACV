# -*- coding: utf-8 -*-
"""
Script d'application des courbes sur une image
"""
import os
import argparse
import struct
import math
from osgeo import gdal
import numpy as np
from scipy.interpolate import interp1d, make_interp_spline

# doc du format ACV
# https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/


def read_args():
    """Gestion des arguments"""

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="input image folder")
    parser.add_argument("-o", "--output", required=True, help="output folder")
    parser.add_argument(
        "-c",
        "--curve",
        required=True,
        help="curves to apply to the image (init.tif,bde5_2452.0.acv,bde5_2452.0.0.psb)",
    )
    parser.add_argument(
        "-a",
        "--acv",
        required=True,
        help="path of folder containing acv files and masks (compatible format with GDAL)",
    )
    parser.add_argument(
        "-b",
        "--blocksize",
        required=False,
        default=1000,
        type=int,
        help="number of lines per block",
    )
    parser.add_argument(
        "-q",
        "--quality",
        required=False,
        default=100,
        type=int,
        help="Jpeg compression quality (100: No compression)",
    )

    parser.add_argument("-v", "--verbose", help="verbose (default: 0)", type=int, default=0)
    args = parser.parse_args()

    if args.verbose >= 1:
        print("\nArguments: ", args)

    return args


def load_acv(nom):
    """lecture des courbes dans un fichier ACV"""
    struct_io = struct.Struct(">h")
    acv = {}
    with open(nom, "rb") as fic:
        buffer = fic.read(2)
        acv["type_acv"] = struct_io.unpack(buffer)[0]
        buffer = fic.read(2)
        nb_courbes = struct_io.unpack(buffer)[0]
        courbes = []
        for _idcourbe in range(nb_courbes):
            buffer = fic.read(2)
            nb_pts = struct_io.unpack(buffer)[0]
            courbe = []
            for _apt in range(nb_pts):
                buffer = fic.read(2)
                pt_sortie = struct_io.unpack(buffer)[0]
                buffer = fic.read(2)
                pt_entree = struct_io.unpack(buffer)[0]
                courbe.append(pt_entree)
                courbe.append(pt_sortie)
            courbes.append(courbe)
        acv["courbes"] = courbes
        return acv


def create_lut():
    """creation des 3 luts (R, V, B) avec des fonctions identités"""
    lut_r = np.arange(256)
    lut_v = np.arange(256)
    lut_b = np.arange(256)
    return [lut_r, lut_v, lut_b]


def apply(lut, courbe):
    """modification d'une lut pour l'application d'une courbe"""
    fct = interp1d(courbe[::2], courbe[1::2])
    if len(courbe) > 4:
        order, value = (
            [(2, 0)],
            [(2, 0)],
        )  # natural spline boundary conditions
        fct = make_interp_spline(courbe[::2], courbe[1::2], k=3, bc_type=(order, value))
    for level in range(256):
        lut[level] = np.round(fct(lut[level]))


def apply_all(image, courbes, output, block_size):
    """application des courbes courbes avec le masque masque sur l'image."""
    print("application des luts par blocs...")
    nb_bands = image.RasterCount

    # on charge une portion de l'image
    nb_block = int(math.ceil(image.RasterYSize / block_size))
    for block in range(nb_block):
        print("bloc : ", block)
        image_b = image.ReadAsArray(
            0,
            block * block_size,
            image.RasterXSize,
            min(image.RasterYSize - block * block_size, block_size),
        )
        if nb_bands == 1:
            image_b = np.array([image_b])
        # on applique toutes les courbes sur cette portion d'image
        for courbe in courbes:
            lut = courbe["lut"]
            masque = courbe["masque"]
            if masque is not None:
                masque_b = masque.ReadAsArray(
                    0,
                    block * block_size,
                    masque.RasterXSize,
                    min(masque.RasterYSize - block * block_size, block_size),
                )
                a_1 = masque_b / 255.0
                a_2 = (-masque_b + 255) / 255.0
                for k in range(nb_bands):
                    image_b[k] = np.round(
                        np.multiply(a_1, np.take(lut[k], image_b[k])) + np.multiply(a_2, image_b[k])
                    )
            else:
                for k in range(nb_bands):
                    image_b[k] = np.take(lut[k], image_b[k])
        # ecriture des blocs dans l'image en memoire
        for k in range(nb_bands):
            output.GetRasterBand(k+1).WriteArray(np.round(image_b[k]), 0, block * block_size)
        print("...fait")
    print("fin du traitement des blocs")


def preparation(a_line):
    """préparation des luts et des masques pour toutes les courbes."""
    T = a_line.split(",")
    nb_acv = int((len(T) - 1) / 2)
    print("nombre de courbes: ", nb_acv)
    courbes = []
    for i in range(nb_acv):
        num_acv = nb_acv - 1 - i
        nom_acv = os.path.join(dir_acv, T[1 + 2 * num_acv])
        ACV = load_acv(nom_acv)
        print("application de la courbe : ", nom_acv)
        print("preparation des luts...")
        lut = create_lut()
        apply(lut[0], ACV["courbes"][1])
        apply(lut[1], ACV["courbes"][2])
        apply(lut[2], ACV["courbes"][3])
        # l'ordre a été repris sur l'implémentation faite dans le socle
        # http://gitlab.forge-idi.ign.fr/socle/sd-socle/blob/dev/src/ign/image/radiometry/AcvCurveTransform.cpp
        # on applique d'abord la courbe du canal, puis la courbe RVB
        apply(lut[0], ACV["courbes"][0])
        apply(lut[1], ACV["courbes"][0])
        apply(lut[2], ACV["courbes"][0])
        print("...application des luts faite")
        masque = None
        if len(T[2 + 2 * num_acv]) > 2:
            nom_alpha = os.path.join(dir_acv, T[2 + 2 * num_acv]).replace(".psb", ".tif")
            print("utilisation du masque : [", nom_alpha, "]")
            masque = gdal.Open(nom_alpha)
        courbes.append({"lut": lut, "masque": masque})
        print("...fait")
    return courbes


ARGS = read_args()

dir_acv = os.path.splitext(ARGS.acv)[0]
id_image = ARGS.curve.split(",")[0]
nom_img = os.path.join(ARGS.input, id_image)

IMAGE = gdal.Open(nom_img)
geo_trans = IMAGE.GetGeoTransform()
OUTPUT = gdal.GetDriverByName("MEM").Create(
    "", IMAGE.RasterXSize, IMAGE.RasterYSize, IMAGE.RasterCount, gdal.GDT_Byte
)
if geo_trans and geo_trans != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
    OUTPUT.SetGeoTransform(geo_trans)

COURBES = preparation(ARGS.curve)

apply_all(IMAGE, COURBES, OUTPUT, ARGS.blocksize)
nom_out = os.path.join(ARGS.output, id_image)

if ARGS.quality < 100:
    gdal.GetDriverByName("COG").CreateCopy(
        nom_out, OUTPUT, options=["QUALITY=" + str(ARGS.quality), "COMPRESS=JPEG"]
    )
else:
    gdal.GetDriverByName("COG").CreateCopy(nom_out, OUTPUT)
