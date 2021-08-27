#!/usr/bin/env python3
"""
Purpose: Unit testing for geoimage.py
Author : Chris Schnaufer <schnaufer@arizona.edu>
Notes:
    This file assumes it's in a subfolder off the main folder
"""
import json
import os
import subprocess
import numpy as np
import pytest
from numpy import nan
from osgeo import gdal, ogr

from agpypeline import geoimage, geometries

TEST_FILES = ['agpypeline/geoimage.py', 'agpypeline/geometries.py']
TEST_IMAGE = os.path.realpath('images/output.tin.tif')
JSON_FILE = os.path.realpath('data/geometries.json')


def test_exists():
    """Tests whether all necessary files are accessible"""
    for file in TEST_FILES:
        assert os.path.isfile(file)
    assert os.path.isfile(TEST_IMAGE) and os.path.isfile(JSON_FILE)


def test_geoimage_clip_raster():
    """Checks the dimensions when calling clip_raster"""
    if os.path.isfile("images/test_geoimage_clip_raster.tif"):
        os.remove("images/test_geoimage_clip_raster.tif")
    new_image = "images/test_geoimage_clip_raster.tif"
    # pylint: disable=consider-using-with
    open(new_image, 'w', encoding='utf-8')
    src = gdal.Open(TEST_IMAGE)
    ulx, xres, _, uly, _, yres = src.GetGeoTransform()
    lrx = ulx + (src.RasterXSize * xres)
    lry = uly + (src.RasterYSize * yres)
    gps_bounds = (lry + (uly - lry) / 4, lry + 3 * (uly - lry) / 4, ulx + (lrx - ulx) / 4, ulx + 3 * (lrx - ulx) / 4)
    geoimage.clip_raster(TEST_IMAGE, gps_bounds, new_image)
    check_result = os.system("gdalinfo images/orig_geoimage_clip_raster.tif")
    new_output = os.system("gdalinfo images/test_geoimage_clip_raster.tif")
    if os.path.isfile("images/test_geoimage_clip_raster.tif.aux.xml"):
        os.remove("images/test_geoimage_clip_raster.tif.aux.xml")
    assert check_result == new_output


def test_geoimage_clip_raster_intersection():
    """Checks the output when calling clip_raster_intersection on an image, using metadata from the data folder
    in order to make sure that the function output is correct"""
    file_bounds = geoimage.get_image_bounds(TEST_IMAGE)
    with open(JSON_FILE, encoding='utf-8') as in_file:
        geo_json = json.load(in_file)
    for feature in range(len(geo_json["features"])):
        geometry = geo_json["features"][feature]["geometry"]
        plot_bounds = ogr.CreateGeometryFromJson(str(geometry))
        no_overlap_result = geoimage.clip_raster_intersection(TEST_IMAGE, file_bounds, plot_bounds,
                                                              "images/geoimage_clip_raster_intersection.tif")
        assert no_overlap_result is None
    complete_overlap = geoimage.clip_raster_intersection(TEST_IMAGE, file_bounds, file_bounds,
                                                         "images/geoimage_clip_raster_intersection.tif")
    with open("data/geoimage_clip_raster_intersection.json", 'r', encoding='utf-8') as result_file:
        check_result = json.load(result_file)
    assert check_result["complete_overlap"] == str(complete_overlap)
    new_image_bounds = geoimage.get_image_bounds("images/test_geoimage_clip_raster.tif")
    partial_overlap = geoimage.clip_raster_intersection(TEST_IMAGE, file_bounds, new_image_bounds,
                                                        "images/geoimage_clip_raster_intersection.tif")
    assert check_result["partial_overlap"] == str(partial_overlap)


def test_geoimage_clip_raster_intersection_json():
    """Checks the output when calling clip_raster_intersection_json on an image, usingmetadata from the
    data folder in order to make sure that the function output is correct"""
    file_bounds = geoimage.get_image_bounds(TEST_IMAGE)
    json_file_bounds = str(json.loads(geometries.geometry_to_geojson(file_bounds)))
    with open(JSON_FILE, encoding='utf-8') as in_file:
        geo_json = json.load(in_file)
    for feature in range(len(geo_json["features"])):
        json_plot_bounds = json.dumps(geo_json["features"][feature]["geometry"])
        no_overlap_result = geoimage.clip_raster_intersection_json(TEST_IMAGE, json_file_bounds, json_plot_bounds,
                                                                   "images/geoimage_clip_raster_intersection_json.tif")
        assert no_overlap_result is None
    complete_overlap = geoimage.clip_raster_intersection_json(TEST_IMAGE, json_file_bounds, json_file_bounds,
                                                              "images/geoimage_clip_raster_intersection_json.tif")
    with open("data/geoimage_clip_raster_intersection_json.json", 'r', encoding='utf-8') as result_file:
        check_result = json.load(result_file)
    assert check_result["complete_overlap"] == str(complete_overlap)
    new_image_bounds = geoimage.get_image_bounds("images/test_geoimage_clip_raster.tif")
    json_new_image_bounds = str(json.loads(geometries.geometry_to_geojson(new_image_bounds)))
    partial_overlap = geoimage.clip_raster_intersection_json(TEST_IMAGE, json_file_bounds, json_new_image_bounds,
                                                             "images/geoimage_clip_raster_intersection.tif")
    assert check_result["partial_overlap"] == str(partial_overlap)


def test_geoimage_create_geotiff():
    """Tests create_geotiff, although a complete image is not generated at the moment. The coordinates used are
    from gdal.open(TEST_IMAGE).GetGeoTransform()"""
    src = gdal.Open(TEST_IMAGE)
    # pylint: disable=unused-variable
    ulx, xres, _, uly, _, yres = src.GetGeoTransform()
    lrx = ulx + (src.RasterXSize * xres)
    lry = uly + (src.RasterYSize * yres)
    gps_bounds = (lry + (uly - lry) / 4, lry + 3 * (uly - lry) / 4, ulx + (lrx - ulx) / 4, ulx + 3 * (lrx - ulx) / 4)
    raster_array = np.array(src.GetRasterBand(1).ReadAsArray())
    if os.path.isfile("images/geoimage_create_geotiff.tif"):
        os.remove("images/geoimage_create_geotiff.tif")
    geoimage.create_geotiff(raster_array, gps_bounds, out_path="images/geoimage_create_geotiff.tif", srid=26913,
                            nodata=-9999)
    check_output = subprocess.check_output(['gdalinfo', 'images/geoimage_create_geotiff_orig.tif']).decode("utf-8")
    check_output_lines = check_output.splitlines()
    orig_out = check_output_lines[:1] + check_output_lines[2:]
    new_output = subprocess.check_output(['gdalinfo', 'images/geoimage_create_geotiff.tif']).decode("utf-8")
    new_output_lines = new_output.splitlines()
    new_out = new_output_lines[:1] + new_output_lines[2:]
    assert orig_out == new_out


def test_geoimage_create_tiff():
    """Tests create_tiff"""
    src = gdal.Open(TEST_IMAGE)
    # pylint: disable=unused-variable
    raster_array = np.array(src.GetRasterBand(1).ReadAsArray())
    if os.path.isfile("images/geoimage_create_tiff.tif"):
        os.remove("images/geoimage_create_tiff.tif")
    geoimage.create_tiff(raster_array, out_path="images/geoimage_create_tiff.tif", nodata=-9999)
    dst = gdal.Open("images/geoimage_create_tiff.tif")
    dst_array = np.array(dst.GetRasterBand(1).ReadAsArray())
    assert dst_array.shape == raster_array.shape


def test_geoimage_get_epsg():
    """Test to see whether get_epsg correctly locates the epsg from a geotiff image"""
    epsg = geoimage.get_epsg(TEST_IMAGE)
    assert epsg == "26913"


def test_geoimage_get_image_bounds():
    """Tests get_image_bounds on a geotiff image and makes sure that the correct polygons are returned"""
    bad_file_res = geoimage.get_image_bounds("")
    assert bad_file_res is None
    res = geoimage.get_image_bounds(TEST_IMAGE)
    with open("data/geoimage_get_image_bounds.json", encoding='utf-8') as result_file:
        check_arr = json.load(result_file)
    assert str(res) == check_arr[0]
    res2 = geoimage.get_image_bounds(TEST_IMAGE, 3614)
    assert str(res2) == check_arr[1]


def test_geoimage_get_image_bounds_json():
    """Tests get_image_bounds_json on a geotiff file against output from a .json file in the data folder"""
    with open("data/geoimage_get_image_bounds_json.json", encoding='utf-8') as result_file:
        check_result = json.load(result_file)
    res = geoimage.get_image_bounds_json(TEST_IMAGE)
    assert str(res) == check_result


def test_geoimage_image_get_geobounds():
    """Tests get_geobounds on both empty input and on a geotiff file"""
    not_found_res = geoimage.image_get_geobounds("")
    assert not_found_res, [nan, nan, nan, nan]
    res = geoimage.image_get_geobounds(TEST_IMAGE)
    with open("data/geoimage_image_get_geobounds.json", encoding='utf-8') as result_file:
        check = json.load(result_file)
    assert res == check


def test_geoimage_get_centroid_latlon():
    """Tests get_centroid_latlon from geoimage.py and
    make_centroid_geometry in geometries.py. It is checked
    whether the function raises errors in order to ensure
    that error blocks are reached, and valid output is also
    checked"""
    with pytest.raises(RuntimeError) as excinfo:
        geoimage.get_centroid_latlon("")
    assert "File is not a geo-referenced image file: " in str(excinfo.value)
    with pytest.raises(RuntimeError) as excinfo:
        jpg_file = "images/jpg_images/DJI_0340.JPG"
        geoimage.get_centroid_latlon(jpg_file)
    assert "File is not a geo-referenced image file: " + jpg_file in str(excinfo.value)
    res = geoimage.get_centroid_latlon(TEST_IMAGE)
    assert str(res) == "POINT (-106.44744820025 35.8862725499103)"
