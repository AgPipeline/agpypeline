#!/usr/bin/env python3
"""
Purpose: Unit testing for entrypoint.py
Author : Chris Schnaufer <schnaufer@arizona.edu>
Notes:
    This file assumes it's in a subfolder off the main folder
"""
import argparse
import json
import os
import piexif

from agpypeline import configuration, environment

TEST_FILES = ['agpypeline/configuration.py', 'agpypeline/environment.py']


def test_exists():
    """Tests whether all necessary files are accessible"""
    for file in TEST_FILES:
        assert os.path.isfile(file)


def test_environment_exif_tags_to_timestamp():
    """Tests environment's exif_tags_to_timestamp function py processing image information in order
    to extract the image's exif tags and then checking the function call on the exif tags against the
    results from a file in the data directory"""
    arr = []
    environ = environment.__internal__()
    assert environ.exif_tags_to_timestamp({}) is None
    for image in os.listdir("images/jpg_images"):
        if image.endswith(".JPG"):
            tags_dict = piexif.load("images/jpg_images/" + image)
            exif_tags = tags_dict["Exif"]
            result = environ.exif_tags_to_timestamp(exif_tags)
            arr.append(result)
    with open("data/exif_tags_to_timestamp.txt", encoding='utf-8') as checkfile:
        assert str(arr) == checkfile.read()


def test_environment_get_first_timestamp():
    """The image files included do have accessible timestamps until the update takes place, but this will
    check the result when not having a timestamp included and when having a timestamp included"""
    arr = []
    environ = environment.__internal__()
    no_timestamp_res = environ.get_first_timestamp("images/jpg_images/DJI_0340.JPG")
    later_timestamp_res = environ.get_first_timestamp("images/jpg_images/DJI_0340.JPG", '2020-12-31')
    earlier_timestamp_res = environ.get_first_timestamp("images/jpg_images/DJI_0340.JPG", '2000-12-31')
    arr.append(no_timestamp_res)
    arr.append(later_timestamp_res)
    arr.append(earlier_timestamp_res)
    with open("data/environment_get_first_timestamp.json", encoding='utf-8') as in_file:
        checkfile = json.load(in_file)
    assert no_timestamp_res == checkfile[0]
    assert later_timestamp_res == checkfile[1]
    assert earlier_timestamp_res == checkfile[2]


def test_environment_environment():
    """Tests initializing environment's Environment class by making sure it contains all necessary parameters"""
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
    """Tests the call of generate_transformer_md on a default configuration"""
    environ = environment.Environment(configuration.Configuration())
    assert environ.generate_transformer_md() == {'version': None, 'name': None, 'author': None, 'description': None,
                                                 'repository': {'repUrl': None}}


def test_environment_add_parameters():
    """Tests the call of add_parameters with default parameters"""
    parser = argparse.ArgumentParser()
    environ = environment.Environment(configuration.Configuration())
    environ.add_parameters(parser)
    assert parser.epilog == "None version None author None None"


def test_environment_get_transformer_params():
    """Checks the call of get_transformer_parameters with default parameters against the output from a .json file
    list_files is set to None because it is a function, and timestamp is set to none because it is the current
     timestamp, which differs from second to second"""
    with open("data/environment_get_transformer_params.json", encoding='utf-8') as in_file:
        check_result = json.load(in_file)
    environ = environment.Environment(configuration.Configuration())
    namespace = argparse.Namespace()
    namespace.file_list = []
    namespace.working_space = []
    result = environ.get_transformer_params(namespace, [])
    result_dict = {'transformer_md': result['transformer_md'], 'full_md': result['full_md']}
    check_md = dict(result['check_md']._asdict())
    check_md['timestamp'] = ''
    check_md['list_files'] = ''
    result_dict['check_md'] = check_md
    assert check_result == result_dict
