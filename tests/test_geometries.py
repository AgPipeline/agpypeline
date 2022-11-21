#!/usr/bin/env python3
"""
Purpose: Unit testing for geometries.py
Author : Chris Schnaufer <schnaufer@arizona.edu>
Notes:
    This file assumes it's in a subfolder off the main folder
"""
import json
import os

from osgeo import ogr, osr
from shapely.geometry import Point, LineString, MultiPoint

from agpypeline import geometries

TEST_FILES = ['agpypeline/geometries.py']
JSON_FILE = os.path.realpath('data/geometries.json')

# Smallest error allowed when comparing calculated geometry values
GEOM_MIN_ERROR = 0.000000001


def test_exists():
    """Tests whether all necessary files are accessible"""
    for file in TEST_FILES:
        assert os.path.isfile(file)
    assert os.path.isfile(JSON_FILE)


def test_geometries_calculate_centroid_from_wkt():
    """Tests calculate_centroid_from_wkt on a few basic geometries from shapely.geometry"""
    test_point = Point(0, 0)
    wkt = test_point.centroid.wkt
    result = geometries.calculate_centroid_from_wkt(wkt)
    assert result == (0.0, 0.0)
    line = LineString([(2, 0), (2, 4), (3, 4)])
    wkt = line.wkt
    result = geometries.calculate_centroid_from_wkt(wkt)
    assert result == (2.1, 2.4)
    multi = MultiPoint([(0, 0), (1, 1), (1, -1), (1, 0)])
    wkt = multi.wkt
    result = geometries.calculate_centroid_from_wkt(wkt)
    assert result == (0.75, 0.0)


def test_geometries_calculate_overlap_percent():
    """Tests calculate_overlap_percent by trying to overlap the bounds from a json file with themselves and then from
    a modified version of themselves"""
    with open(JSON_FILE, 'r', encoding='utf-8') as in_file:
        loaded_file = json.load(in_file)
        check_bounds = loaded_file["features"][0]["geometry"]
        bounding_box = {"type": "Polygon", "coordinates": [
            [[408989, 3659975], [408990, 3659975], [408990, 3659972], [408989, 3659972], [408989, 3659975]]]}
        assert abs(geometries.calculate_overlap_percent(check_bounds, check_bounds) - 1.0) <= GEOM_MIN_ERROR
        assert abs(round(geometries.calculate_overlap_percent(check_bounds, bounding_box), 4) - 0.7591) <= GEOM_MIN_ERROR


def test_geometries_convert_geometry_from_file():
    """Tests convert_geometry by checking the function call on geometries contained within a loaded .json file
    against a file containing function call results"""
    null_input_test = geometries.convert_geometry(None, None)
    assert null_input_test is None
    with open(JSON_FILE, 'r', encoding='utf-8') as in_file:
        loaded_file = json.load(in_file)
    epsg = loaded_file["crs"]['properties']['name'].split('::')[-1]
    with open("data/convert_geometry_from_file.json", 'r', encoding='utf-8') as result_file:
        check_result = json.load(result_file)
    for feature in range(len(loaded_file["features"])):
        check_bounds = loaded_file["features"][feature]["geometry"]
        geometry = ogr.CreateGeometryFromJson(str(check_bounds))
        srs = osr.SpatialReference()
        srs.SetFromUserInput("EPSG:" + epsg)
        result = geometries.convert_geometry(geometry, srs)
        assert check_result[str(feature)] == str(result)


def test_geometries_convert_geometry_from_polygon():
    """Tests convert_geometry by checking the function call on geometries
    created from ogr.Geometry and spatial references created from
    osr.SpatialReference against a file containing function call results"""
    with open("data/convert_geometry_from_polygon.json", 'r', encoding='utf-8') as result_file:
        check_result = json.load(result_file)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(1, 0)
    ring.AddPoint(0, 1)
    ring.AddPoint(-1, 0)
    ring.AddPoint(0, -1)
    ring.AddPoint(1, 0)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    assert poly.IsValid()
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)
    poly.AssignSpatialReference(source)
    result = geometries.convert_geometry(poly, source)
    check1 = geometries.geometry_to_tuples(result)
    assert check_result["same_epsg"] == list(check1)
    source2 = osr.SpatialReference()
    source2.ImportFromEPSG(3857)
    result2 = geometries.convert_geometry(poly, source2)
    check2 = geometries.geometry_to_tuples(result2)
    different_epsg = check_result["different_epsg"]
    for i in range(len(list(check2))):
        assert abs(check2[i] - different_epsg[i]) <= GEOM_MIN_ERROR


def test_geometries_geometry_to_tuples():
    """Tests geometry_to_tuples by checking the function call on geometries contained within a loaded .json file
    against a file containing function call results"""
    with open(JSON_FILE, 'r', encoding='utf-8') as in_file:
        loaded_file = json.load(in_file)
    with open("data/geometry_to_tuples.json", 'r', encoding='utf-8') as result_file:
        check_result = json.load(result_file)
    for feature in range(len(loaded_file["features"])):
        check_bounds = loaded_file["features"][feature]["geometry"]
        geometry = ogr.CreateGeometryFromJson(str(check_bounds))
        result = geometries.geometry_to_tuples(geometry)
        assert tuple(check_result[str(feature)]) == result


def test_geometries_geojson_to_tuples():
    """Tests geojson_to_tuples by checking the function call on geometries contained within a loaded .json file
    against a file containing function call results"""
    with open(JSON_FILE, 'r', encoding='utf-8') as in_file:
        loaded_file = json.load(in_file)
    with open("data/geojson_to_tuples.json", 'r', encoding='utf-8') as result_file:
        check_result = json.load(result_file)
    for feature in range(len(loaded_file["features"])):
        check_bounds = str(loaded_file["features"][feature]["geometry"])
        result = geometries.geojson_to_tuples(check_bounds)
        assert check_result[str(feature)] == str(result)


def test_geometries_geometry_to_geojson():
    """Tests geometry_to_geojson by checking the function call on geometries contained within a loaded .json file
    against a file containing function call results"""
    with open(JSON_FILE, 'r', encoding='utf-8') as in_file:
        loaded_file = json.load(in_file)
    with open("data/geometry_to_geojson.json", 'r', encoding='utf-8') as result_file:
        check_result = json.load(result_file)
    for feature in range(len(loaded_file["features"])):
        check_bounds = loaded_file["features"][feature]["geometry"]
        geometry = ogr.CreateGeometryFromJson(str(check_bounds))
        result = geometries.geometry_to_geojson(geometry)
        assert check_result[str(feature)] == result


def test_geometries_polygon_from_ring():
    """Tests polygon_from_ring both using empty parameters and by creating an ring as ogr.Geometry"""
    ring = ogr.Geometry(ogr.wkbLinearRing)
    without_points_or_epsg = geometries.polygon_from_ring(ring)
    assert str(without_points_or_epsg) == "POLYGON EMPTY"
    ring.AddPoint(1179091.1646903288, 712782.8838459781)
    ring.AddPoint(1161053.0218226474, 667456.2684348812)
    ring.AddPoint(1214704.933941905, 641092.8288590391)
    ring.AddPoint(1228580.428455506, 682719.3123998424)
    ring.AddPoint(1218405.0658121984, 721108.1805541387)
    ring.AddPoint(1179091.1646903288, 712782.8838459781)
    good_epsg = geometries.polygon_from_ring(ring, 3857)
    with open("data/geometries_polygon_from_ring.json", encoding='utf-8') as check_result:
        assert str(good_epsg) == json.load(check_result)
