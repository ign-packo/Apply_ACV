#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'application des courbes sur une image
"""
import sys
from osgeo import gdal
import numpy as np


# doc du format ACV
# https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/


def load_image(nom):
    """chargement d'une image avec son georef"""
    fic = gdal.Open(nom)
    return fic.ReadAsArray().astype("int32"), fic.GetGeoTransform()


def save_image(nom, image, _geo_trans):
    """sauvegarde d'une image avec son georef"""
    if len(image.shape) == 2:
        cols = image.shape[1]
        rows = image.shape[0]
        bands = 1
        image = np.array([image])
    else:
        cols = image.shape[2]
        rows = image.shape[1]
        bands = image.shape[0]
    print(bands, cols, rows)
    driver = gdal.GetDriverByName("GTiff")
    out_raster = driver.Create(nom, cols, rows, bands, gdal.GDT_Byte)
    for i in range(bands):
        band = out_raster.GetRasterBand(i+1)
        band.WriteArray(image[i].astype("uint8"))


img_1, ref = load_image(sys.argv[1])
img_2, ref = load_image(sys.argv[2])
diff = np.absolute(img_1 - img_2)
e_max = np.max(diff)
if e_max > 0:
    print('Attention, ecart max : ', e_max)
    save_image('ecart.tif', diff, None)
    sys.exit(1)
print('Pas de difference')
