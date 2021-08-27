#!/usr/bin/env python3
"""
Purpose: Unit testing for geometries.py
Author : Chris Schnaufer <schnaufer@arizona.edu>
Notes:
    This file assumes it's in a subfolder off the main folder
"""
import json
import os
import subprocess

from agpypeline import lasfile

TEST_FILES = ['agpypeline/geometries.py']


def test_exists():
    """Tests whether all necessary files are accessible"""
    for file in TEST_FILES:
        assert os.path.isfile(file)


def test_lasfile_get_las_epsg_from_header():  # More tests might be needed in order to know if it works for a null epsg
    """Tests whether an epsg can be successfully retrieved from a .las file"""
    assert lasfile.get_las_epsg("images/output.tin.tif") is None
    assert lasfile.get_las_epsg("images/interesting.las") == '4326'
    if os.path.isfile("images/output.tin.tif.aux.xml"):
        os.remove("images/output.tin.tif.aux.xml")


def test_lasfile_clip_las():
    """A .las file is needed but is not able to be pushed to GitHub because it is too large"""
    las_info = subprocess.run(['pdal', 'info', 'images/interesting.las'], stderr=subprocess.PIPE,
                              stdout=subprocess.PIPE, check=True)
    las_info_decoded = json.loads(las_info.stdout.decode())
    bounds = las_info_decoded['stats']['bbox']['native']['bbox']
    try:
        min_x = bounds['minx']
        max_x = bounds['maxx']
        min_y = bounds['miny']
        max_y = bounds['maxy']
        clip_min_x = min_x + (max_x - min_x) * 0.25
        clip_max_x = min_x + (max_x - min_x) * 0.75
        clip_min_y = min_y + (max_y - min_y) * 0.25
        clip_max_y = min_y + (max_y - min_y) * 0.75
        lasfile.clip_las("images/interesting.las",
                         (clip_min_x, clip_max_x, clip_min_y, clip_max_y), "images/clip_las_out.las")
        new_las_info = subprocess.run(['pdal', 'info', 'images/clip_las_out.las'], stderr=subprocess.PIPE,
                                      stdout=subprocess.PIPE, check=True)
        new_las_info_decoded = json.loads(new_las_info.stdout.decode())
        new_bounds = new_las_info_decoded['stats']['bbox']['native']['bbox']
        assert abs(new_bounds['minx'] - clip_min_x) / new_bounds['minx'] < 0.01
        assert abs(new_bounds['maxx'] - clip_max_x) / new_bounds['maxx'] < 0.01
        assert abs(new_bounds['miny'] - clip_min_y) / new_bounds['miny'] < 0.01
        assert abs(new_bounds['maxy'] - clip_max_y) / new_bounds['maxy'] < 0.01
    except KeyError:
        assert False
    finally:
        if os.path.isfile("images/clip_las_out.las"):
            os.remove("images/clip_las_out.las")


def test_lasfile_get_las_extents():
    """Get the extents of a LAS file"""
    with open("data/lasfile_get_las_extents.json", encoding='utf-8') as in_file:
        check_output = json.load(in_file)
    result = lasfile.get_las_extents("images/interesting.las", 4326)
    json_result = json.loads(result)
    assert check_output == json_result
