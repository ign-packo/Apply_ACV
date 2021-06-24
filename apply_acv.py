# -*- coding: utf-8 -*-
"""
Script d'application des courbes sur une image
"""
import os
import sys
import struct
from osgeo import gdal
import numpy as np
from scipy.interpolate import interp1d, make_interp_spline

# doc du format ACV
# https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/


def load_image(nom):
    """chargement d'une image avec son georef"""
    print("load_image : [", nom, "]")
    fic = gdal.Open(nom)
    return fic.ReadAsArray(), fic.GetGeoTransform()


def save_image(nom, image, geo_trans):
    """sauvegarde d'une image avec son georef"""
    cols = image.shape[2]
    rows = image.shape[1]
    bands = image.shape[0]
    print(bands, cols, rows)
    driver = gdal.GetDriverByName("GTiff")
    out_raster = driver.Create(nom, cols, rows, bands, gdal.GDT_Byte)
    if geo_trans and geo_trans != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
        out_raster.SetGeoTransform(geo_trans)
    band = out_raster.GetRasterBand(1)
    band.WriteArray(np.round(image[0]))
    band = out_raster.GetRasterBand(2)
    band.WriteArray(np.round(image[1]))
    band = out_raster.GetRasterBand(3)
    band.WriteArray(np.round(image[2]))


def load_acv(nom):
    """"lecture des courbes dans un fichier ACV"""
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
    return lut_r, lut_v, lut_b


def apply(lut, courbe):
    """modification d'une lut pour l'application d'une courbe """
    fct = interp1d(courbe[::2], courbe[1::2])
    if len(courbe) > 4:
        order, value = (
            [(2, 0)],
            [(2, 0)],
        )  # natural spline boundary conditions
        fct = make_interp_spline(
            courbe[::2], courbe[1::2], k=3, bc_type=(order, value)
        )
    for level in range(256):
        lut[level] = np.round(fct(lut[level]))


def apply_all(image, courbes, masque):
    """application des courbes courbes avec le masque masque sur l'image."""
    print("preparation des luts...")
    print(courbes)
    lut_r, lut_v, lut_b = create_lut()
    apply(lut_r, courbes["courbes"][1])
    apply(lut_v, courbes["courbes"][2])
    apply(lut_b, courbes["courbes"][3])
    # l'ordre a été repris sur l'implémentation faite dans le socle
    # http://gitlab.forge-idi.ign.fr/socle/sd-socle/blob/dev/src/ign/image/radiometry/AcvCurveTransform.cpp
    # on applique d'abord la courbe du canal, puis la courbe RVB
    apply(lut_r, courbes["courbes"][0])
    apply(lut_v, courbes["courbes"][0])
    apply(lut_b, courbes["courbes"][0])
    print("...fait")
    print("application des luts...")
    if masque is not None:
        a_1 = masque / 255.0
        a_2 = (-masque + 255) / 255.0
        image[0] = np.round(
            np.multiply(a_1, np.take(lut_r, image[0]))
            + np.multiply(a_2, image[0])
        )
        image[1] = np.round(
            np.multiply(a_1, np.take(lut_v, image[1]))
            + np.multiply(a_2, image[1])
        )
        image[2] = np.round(
            np.multiply(a_1, np.take(lut_b, image[2]))
            + np.multiply(a_2, image[2])
        )
    else:
        image[0] = np.take(lut_r, image[0])
        image[1] = np.take(lut_v, image[1])
        image[2] = np.take(lut_b, image[2])
    print("...fait")


fichier = sys.argv[1]
dir_in = sys.argv[2]
dir_out = sys.argv[3]

dir_acv = os.path.splitext(fichier)[0]

for line in open(fichier):
    T = line.split(",")
    print(T)
    nom_img = os.path.join(dir_in, T[0])
    img, geoTrans = load_image(nom_img)
    nbAcv = int((len(T) - 1) / 2)
    print("nombre de courbes: ", nbAcv)
    for i in range(nbAcv):
        num_acv = nbAcv - 1 - i
        nom_acv = os.path.join(dir_acv, T[1 + 2 * num_acv])
        ACV = load_acv(nom_acv)
        print("application de la courbe : ", nom_acv)
        if len(T[2 + 2 * num_acv]) > 2:
            nom_alpha = os.path.join(dir_acv, T[2 + 2 * num_acv]).replace(
                ".psb", ".tif"
            )
            print("utilisation du masque : [", nom_alpha, "]")
            alpha, geo = load_image(nom_alpha)
            apply_all(img, ACV, alpha)
        else:
            print("sans masque")
            apply_all(img, ACV, None)
    nom_out = os.path.join(dir_out, T[0])
    save_image(nom_out, img, geoTrans)
