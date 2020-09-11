#!/usr/bin/env python3
"""
Purpose: Unit testing for agpypeline files
Author : Chris Schnaufer <schnaufer@arizona.edu>
Notes:
    This file assumes it's in a subfolder off the main folder
"""
import argparse
import datetime
import json
import os
import piexif
import subprocess

from agpypeline import algorithm
from agpypeline import configuration
from agpypeline import entrypoint
from agpypeline import environment
from agpypeline import geoimage
from agpypeline import geometries
from agpypeline import lasfile
import numpy as np
from numpy import nan
from liblas.header import Header
from osgeo import gdal, ogr, osr
from shapely.geometry import Point, LineString, MultiPoint

TEST_FILES = ['agpypeline/algorithm.py', 'agpypeline/configuration.py',
              'agpypeline/entrypoint.py', 'agpypeline/environment.py', 'agpypeline/geoimage.py',
              'agpypeline/geometries.py', 'agpypeline/lasfile.py']

JSON_FILE = os.path.realpath('data/geometries.json')

TEST_IMAGE = os.path.realpath('images/output.tin.tif')

TEST_METADATA = os.path.realpath('data/08f445ef-b8f9-421a-acf1-8b8c206c1bb8_metadata_cleaned.json')


def test_exists():
    for file in TEST_FILES:
        assert os.path.isfile(file)
    assert os.path.isfile(JSON_FILE) and os.path.isfile(TEST_IMAGE) and os.path.isfile(TEST_METADATA)


# Other methods can be used here if wanted in order to test if the error is raised, but this would
# require creating a class
def test_algorithm():
    alg = algorithm.Algorithm()
    try:
        alg.perform_process(environment.Environment(configuration.Configuration()), {}, {}, [])
        assert True is False
    except RuntimeError as error:
        assert str(error) == "The Algorithm class method perform_process() must be overridden by a derived class"


def test_configuration():
    config = configuration.Configuration
    for entry in ['transformer_version', 'transformer_description', 'transformer_name', 'transformer_sensor',
                  'transformer_type', 'author_name', 'author_email', 'contributors', 'repository']:
        assert hasattr(config, entry)
        if entry == 'contributors':
            assert getattr(config, entry) == []
        else:
            assert getattr(config, entry) is None


def test_entrypoint_handle_error():
    entry = entrypoint.__internal__()
    bad_result = entry.handle_error(None, None)
    assert bad_result == {'error': 'An error has occurred with error code (-1)', 'code': -1}
    result = entry.handle_error(0, "test message")
    assert result == {'error': 'test message', 'code': 0}


def test_entrypoint_load_metadata():
    entry = entrypoint.__internal__()
    orig = json.load(open("data/entrypoint_load_metadata_files.json"))
    bad_result = entry.load_metadata("")
    assert bad_result == {'error': "Unable to load metadata file ''"}
    result = entry.load_metadata("data/08f445ef-b8f9-421a-acf1-8b8c206c1bb8_metadata_cleaned.json")
    same = False
    if orig == result:
        same = True
    assert same is True


def test_entrypoint_check_params_result_error():
    entry = entrypoint.__internal__()
    result_none = entry.check_params_result_error({})
    assert result_none is None
    result_code = entry.check_params_result_error({'code': 0})
    assert result_code == {'error': 'Error returned from get_transformer_params with code: 0', 'code': -104}
    result_code_and_error = entry.check_params_result_error({'code': 0, 'error': 0})
    assert result_code_and_error == {'error': 'An error has occurred with error code (-104)', 'code': -104}


def test_entrypoint_check_retrieve_results_error():
    entry = entrypoint.__internal__()
    result_none = entry.check_retrieve_results_error(None)
    assert result_none is None
    result = entry.check_retrieve_results_error((3, 3))
    assert result is None
    # I think I would need an actual transformer_retrieve argument in order to fully test this


def test_entrypoint_check_metadata_needed():
    entry = entrypoint.__internal__()
    assert entry.check_metadata_needed(configuration.Configuration()) is False


def test_entrypoint_load_metadata_files():
    entry = entrypoint.__internal__()
    assert entry.load_metadata_files([]) == {'metadata': []}
    orig = json.load(open("data/entrypoint_load_metadata_files.json"))
    assert entry.load_metadata_files(["data/08f445ef-b8f9-421a-acf1-8b8c206c1bb8_metadata_cleaned.json"]) == orig


def test_entrypoint_handle_check_continue_parse_continue_result():
    entry = entrypoint.__internal__()
    result = entry.handle_check_continue(algorithm.Algorithm(), environment.Environment(configuration.Configuration()),
                                         {})
    assert result == {}


def test_entrypoint_handle_retrieve_files():
    entry = entrypoint.__internal__()
    result = entry.handle_retrieve_files(environment.Environment(configuration.Configuration()), argparse.Namespace(),
                                         [])
    assert result is None


def test_entrypoint_perform_processing():
    namespace = argparse.Namespace()
    namespace.file_list = []
    namespace.working_space = []
    entry = entrypoint.__internal__()
    try:
        entry.perform_processing(environment.Environment(configuration.Configuration()), algorithm.Algorithm(),
                                 namespace, [])
        assert True is False
    except RuntimeError as error:
        assert str(error) == "The Algorithm class method perform_process() must be overridden by a derived class"


def test_entrypoint_handle_result():
    entry = entrypoint.__internal__()
    assert entry.handle_result({}) == {}
    assert entry.handle_result({}, "", "") == {}


def test_entrypoint_add_parameters():
    parser = argparse.ArgumentParser()
    entrypoint.add_parameters(parser, algorithm.Algorithm(), environment.Environment(configuration.Configuration()))
    assert str(parser.parse_args()) == "Namespace(debug=30, file_list=[], info=30, metadata=None," \
                                       " result='all', working_space=None)"


def test_entrypoint_do_work():
    parser = argparse.ArgumentParser()
    result = entrypoint.do_work(parser, configuration.Configuration, algorithm.Algorithm())
    assert result == {}


# entrypoint_entrypoint did not return anything and calls entrypoint_do_work()


def test_environment_exif_tags_to_timestamp():
    arr = []
    environ = environment.__internal__()
    assert environ.exif_tags_to_timestamp({}) is None
    for image in os.listdir("images/jpg_images"):
        tags_dict = piexif.load("images/jpg_images/" + image)
        exif_tags = tags_dict["Exif"]
        EXIF_ORIGIN_TIMESTAMP = 36867
        value = exif_tags[EXIF_ORIGIN_TIMESTAMP]
        value = value.decode('UTF-8').strip()
        split_char = None
        if " " in value:
            partial = value.split(" ")
            split_char = " "
        elif "T" in value:
            partial = value.split("T")
            split_char = "T"
        if split_char:
            partial_first = partial[0].replace(":", "-")
            value = partial_first + split_char + partial[1]
            exif_tags[EXIF_ORIGIN_TIMESTAMP] = value
        result = environ.exif_tags_to_timestamp(exif_tags)
        arr.append(result)
    with open("data/exif_tags_to_timestamp.txt", 'r') as checkfile:
        assert str(arr) == checkfile.read()


def test_environment_environment():
    environ = environment.Environment(configuration.Configuration())
    assert environ.sensor is None
    assert environ.args is None
    for entry in ['transformer_version', 'transformer_description', 'transformer_name', 'transformer_sensor',
                  'transformer_type', 'author_name', 'author_email', 'contributors', 'repository']:
        assert hasattr(environ.configuration, entry)
        if entry == 'contributors':
            assert getattr(environ.configuration, entry) == []
        else:
            assert getattr(environ.configuration, entry) is None


def test_environment_generate_transformer_md():
    environ = environment.Environment(configuration.Configuration())
    assert environ.generate_transformer_md() == {'version': None, 'name': None, 'author': None, 'description': None,
                                                 'repository': {'repUrl': None}}


def test_environment_add_parameters():
    parser = argparse.ArgumentParser()
    environ = environment.Environment(configuration.Configuration())
    environ.add_parameters(parser)
    assert parser.epilog == "None version None author None None"


def test_environment_get_transformer_params():
    orig = json.load(open("data/environment_get_transformer_params.json"))
    environ = environment.Environment(configuration.Configuration())
    namespace = argparse.Namespace()
    namespace.file_list = []
    namespace.working_space = []
    result = environ.get_transformer_params(namespace, [])
    result['check_md']["list_files"] = None
    result['check_md']["timestamp"] = None
    assert orig == result


def test_geoimage_clip_raster():
    result = geoimage.clip_raster(TEST_IMAGE, (0, 0, 0, 0))
    assert len(result) == 730 and len(result[0]) == 891


def test_geoimage_clip_raster_intersection():
    file_bounds = geoimage.get_image_bounds(TEST_IMAGE)
    geo_json = json.load(open(JSON_FILE))
    for feature in range(len(geo_json["features"])):
        geometry = geo_json["features"][feature]["geometry"]
        plot_bounds = ogr.CreateGeometryFromJson(str(geometry))
        bad_result = geoimage.clip_raster_intersection(TEST_IMAGE, file_bounds, plot_bounds,
                                                       "images/geoimage_clip_raster_intersection.tif")
        assert bad_result is None
    complete_overlap = str(geoimage.clip_raster_intersection(TEST_IMAGE, file_bounds, file_bounds,
                                                             "images/geoimage_clip_raster_intersection.tif"))
    with open("data/geoimage_clip_raster_intersection.txt", 'r') as checkfile:
        checkfile_content = checkfile.read()
        assert checkfile_content == complete_overlap


def test_geoimage_clip_raster_intersection_json():
    file_bounds = geoimage.get_image_bounds(TEST_IMAGE)
    json_file_bounds = geometries.geometry_to_geojson(file_bounds)
    geo_json = json.load(open(JSON_FILE))
    for feature in range(len(geo_json["features"])):
        json_plot_bounds = geo_json["features"][feature]["geometry"]
        bad_result = geoimage.clip_raster_intersection_json(TEST_IMAGE, json_file_bounds, json_plot_bounds,
                                                            "images/geoimage_clip_raster_intersection.tif")
        assert bad_result is None
    complete_overlap = geoimage.clip_raster_intersection_json(TEST_IMAGE, json_file_bounds, json_file_bounds,
                                                              "images/geoimage_clip_raster_intersection.tif")
    with open("data/geoimage_clip_raster_intersection.txt", 'r') as checkfile:
        checkfile_content = checkfile.read()
        assert checkfile_content == str(complete_overlap)


gps_bounds = (3971937.000, 3972667.000, 368908.000, 369799.000)


def test_geoimage_create_geotiff():
    ds = gdal.Open(TEST_IMAGE)
    myarray = np.array(ds.GetRasterBand(1).ReadAsArray())
    if os.path.isfile("images/output.tif"):
        os.remove("images/output.tif")
    geoimage.create_geotiff(myarray, gps_bounds, "images/output.tif", 26913)


def test_geoimage_get_epsg():
    epsg = geoimage.get_epsg(TEST_IMAGE)
    assert epsg == "26913"


geoimage.get_image_bounds()


# I don't know how to test an input where the file does not have an epsg/epsg = None
def test_geoimage_get_image_bounds():
    bad_file_res = geoimage.get_image_bounds("")
    assert bad_file_res is None
    res = geoimage.get_image_bounds(TEST_IMAGE)
    assert str(res) == "POLYGON ((368908 3972667 0,369799 3972667 0,369799 3971937 0,368908 3971937 0,368908 3972667 " \
                       "0))"
    res2 = geoimage.get_image_bounds(TEST_IMAGE, 3614)
    assert str(res2) == "POLYGON ((368908 3972667 0,369799 3972667 0,369799 3971937 0,368908 3971937 0,368908 3972667 " \
                        "0))"


def test_geoimage_get_image_bounds_json():
    orig = json.load(open("data/geoimage_get_image_bounds_json.json"))
    res = geoimage.get_image_bounds_json(TEST_IMAGE)
    assert str(res) == orig


def test_geoimage_image_get_geobounds():
    not_found_res = geoimage.image_get_geobounds("")
    assert not_found_res, [nan, nan, nan, nan]
    res = geoimage.image_get_geobounds(TEST_IMAGE)
    assert res == [3971937.0, 3972667.0, 368908.0, 369799.0]


def test_geometries_calculate_centroid_from_wkt():
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
    f = json.load(open(JSON_FILE, 'r'))
    check_bounds = f["features"][0]["geometry"]
    bounding_box = {"type": "Polygon", "coordinates": [
        [[408989, 3659975], [408990, 3659975], [408990, 3659972], [408989, 3659972], [408989, 3659975]]]}
    assert geometries.calculate_overlap_percent(check_bounds, check_bounds) == 0.0
    assert round(geometries.calculate_overlap_percent(check_bounds, bounding_box), 4) == 0.7591


def test_geometries_convert_geometry():
    null_input_test = geometries.convert_geometry(None, None)
    assert null_input_test is None
    f = json.load(open(JSON_FILE, 'r'))
    checkfile = json.load(open("data/convert_geometry.json", 'r'))
    for feature in range(len(f["features"])):
        check_bounds = f["features"][feature]["geometry"]
        geometry = ogr.CreateGeometryFromJson(str(check_bounds))
        srs = osr.SpatialReference()
        srs.SetFromUserInput("EPSG:3857")
        result = geometries.convert_geometry(geometry, srs)
        assert checkfile[str(feature)] == str(result)


def test_geometries_geometry_to_tuples():
    f = json.load(open(JSON_FILE, 'r'))
    checkfile = json.load(open("data/geometry_to_tuples.json", 'r'))
    for feature in range(len(f["features"])):
        check_bounds = f["features"][feature]["geometry"]
        geometry = ogr.CreateGeometryFromJson(str(check_bounds))
        result = geometries.geometry_to_tuples(geometry)
        assert tuple(checkfile[str(feature)]) == result


def test_geometries_geojson_to_tuples():
    f = json.load(open(JSON_FILE, 'r'))
    checkfile = json.load(open("data/geojson_to_tuples.json", 'r'))
    for feature in range(len(f["features"])):
        check_bounds = f["features"][feature]["geometry"]
        result = geometries.geojson_to_tuples(check_bounds)
        assert tuple(checkfile[str(feature)]) == result


def func4():
    f = json.load(open(JSON_FILE, 'r'))
    all_jsons = {}
    with open("data/geojson_to_tuples.json", 'w') as outfile:
        for feature in range(len(f["features"])):
            check_bounds = f["features"][feature]["geometry"]
            result = geometries.geojson_to_tuples(str(check_bounds))
            all_jsons[feature] = str(result)
        json.dump(all_jsons, outfile)


def test_geometries_geometry_to_geojson():
    f = json.load(open(JSON_FILE, 'r'))
    checkfile = json.load(open("data/geometry_to_geojson.json", 'r'))
    for feature in range(len(f["features"])):
        check_bounds = f["features"][feature]["geometry"]
        geometry = ogr.CreateGeometryFromJson(str(check_bounds))
        result = geometries.geometry_to_geojson(geometry)
        assert checkfile[str(feature)] == result


# Please let me know if any/all of the data from the geometries.json file falls under the
# "linear ring" category

# Additionally, it mentions that a runtime error is raised if the srid can't be loaded, and
# I am wondering if it is different than the epsg. I have not been able to generate a case where
# None is returned
def test_geometries_polygon_from_ring():
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
    assert str(good_epsg) == "POLYGON ((1179091.16469033 712782.883845978 0,1161053.02182265 667456.268434881" \
                             " 0,1214704.9339419 641092.828859039 0,1228580.42845551 682719.312399842" \
                             " 0,1218405.0658122 721108.180554139 0,1179091.16469033 712782.883845978 0))"


def test_lasfile_clip_las():
    minX = None
    maxX = None
    minY = None
    maxY = None
    lasinfo = subprocess.check_output('lasinfo images/scanner3DTop_L1_ua-mac_2018-06-24__23-24-25-074_merged.las',
                                       shell=True)
    lasinfo_decoded = lasinfo.decode("utf-8")
    split = lasinfo_decoded.splitlines()
    for line in split:
        line_modified = " ".join(line.split())
        line_modified_2 = line_modified.split(" ")
        if line_modified_2[0] == "Min":
            minX = float(line_modified_2[4].replace(",", ""))
            print("minX=", str(minX))
            minY = float(line_modified_2[5].replace(",", ""))
            print("minY=", str(minY))
        elif line_modified_2[0] == "Max":
            maxX = float(line_modified_2[4].replace(",", ""))
            print("maxX=", str(maxX))
            maxY = float(line_modified_2[5].replace(",", ""))
            print("maxY=", str(maxY))
    clip_min_X = minX+(maxX-minX)*0.25
    clip_max_X = minX+(maxX-minX)*0.75
    clip_min_Y = minY+(maxY-minY)*0.25
    clip_max_Y = minY+(maxY-minY)*0.75
    lasfile.clip_las("images/scanner3DTop_L1_ua-mac_2018-06-24__23-24-25-074_merged.las",
                     (clip_min_X, clip_max_X, clip_min_Y, clip_max_Y), "data/clip_las_out.las")


def test_get_las_epsg_from_header(): # More tests might be needed in order to know if it works for a non-null epsg
    header = Header()
    assert lasfile.get_las_epsg_from_header(header) is None


# These are not equal for some reason

def test_get_las_extents():
    check_output = str(json.load(open("data/get_las_extents.json")))
    result = lasfile.get_las_extents("images/scanner3DTop_L1_ua-mac_2018-06-24__23-24-25-074_merged.las", 4326)
    assert check_output == result