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
import string

from agpypeline import algorithm, configuration, entrypoint, environment

TEST_FILES = ['agpypeline/algorithm.py', 'agpypeline/configuration.py',
              'agpypeline/entrypoint.py', 'agpypeline/environment.py']


def test_exists():
    """Tests whether all necessary files are accessible"""
    for file in TEST_FILES:
        assert os.path.isfile(file)


def test_entrypoint_handle_error():
    """Tests entrypoint's handle_error function by passing in an error code and message"""
    entry = entrypoint.__internal__()
    bad_result = entry.handle_error(None, None)
    assert bad_result == {'error': 'An error has occurred with error code (-1)', 'code': -1}
    with open('data/entrypoint_handle_error.json', 'r') as checkfile:
        data = json.load(checkfile)
        letters = list(string.ascii_letters)
        count = 0
        for key in data:
            assert data[key] == entry.handle_error(count, letters[count])
            count += 1


def test_entrypoint_load_metadata():
    """Tests entrypoint's load_metadata function by seeing if the result is the same as a previously called valid
    result"""
    entry = entrypoint.__internal__()
    bad_result = entry.load_metadata("")
    assert bad_result == {'error': "Unable to load metadata file ''"}
    check_result = json.load(open("data/08f445ef-b8f9-421a-acf1-8b8c206c1bb8_metadata_cleaned.json"))
    assert entry.load_metadata("data/08f445ef-b8f9-421a-acf1-8b8c206c1bb8_metadata_cleaned.json")['metadata']\
           == check_result


def test_entrypoint_check_params_result_error():
    """Tests entrypoint's check_params_result_error function by passing in both an entry dictionary and
    a dictionary with a simple error message and code and checking for correct output"""
    entry = entrypoint.__internal__()
    result_none = entry.check_params_result_error({})
    assert result_none is None
    check_result = json.load(open("data/entrypoint_check_params_result_error.json"))
    for i in range(100):
        if i < 50:
            result = entry.check_params_result_error({'code': i})
        else:
            result = entry.check_params_result_error({'code': i, 'error': 99 - i})
        assert check_result[str(i)] == result


def test_entrypoint_check_retrieve_results_error():
    """Tests entrypoint's check_retrieve_results_error function by passing in invalid (and soon valid) retrieve
    values"""
    entry = entrypoint.__internal__()
    result_none = entry.check_retrieve_results_error(None)
    assert result_none is None
    data = json.load(open("data/entrypoint_check_retrieve_results_error.json"))
    for i in range(-75, 50):
        if i < -50:
            result = entry.check_retrieve_results_error((i,))
        else:
            result = entry.check_retrieve_results_error((i, "i is: " + str(i)))
        assert data[str(i)] == result


def test_entrypoint_load_metadata_files():
    """Tests entrypoint's load_metadata_files function by loading both an empty file and a metadata file
    contained in the data folder and asserting that the respective results to the function call are the same
    as these"""
    entry = entrypoint.__internal__()
    assert entry.load_metadata_files([]) == {'metadata': []}
    check_result = json.load(open("data/entrypoint_load_metadata_files.json"))
    assert entry.load_metadata_files(["data/08f445ef-b8f9-421a-acf1-8b8c206c1bb8_metadata_cleaned.json"]) == check_result


def test_entrypoint_handle_check_continue_parse_continue_result():
    """Tests entrypoint's handle_check_continue and parse_continue_result functions by passing in empty class
     instances"""
    entry = entrypoint.__internal__()
    result = entry.handle_check_continue(algorithm.Algorithm(), environment.Environment(configuration.Configuration()),
                                         {})
    assert result == {}


def test_entrypoint_handle_retrieve_files():
    """Tests entrypoint's handle_retrieve_files function by passing in an empty class instances"""
    entry = entrypoint.__internal__()
    result = entry.handle_retrieve_files(environment.Environment(configuration.Configuration()), argparse.Namespace(),
                                         [])
    assert result is None


def test_entrypoint_perform_processing():
    """Tests entrypoint's perform_processing function by passing in empty class instances"""
    namespace = argparse.Namespace()
    namespace.file_list = []
    namespace.working_space = []
    entry = entrypoint.__internal__()
    try:
        result = entry.perform_processing(environment.Environment(configuration.Configuration()), algorithm.Algorithm(),
                                          namespace, [])
    except RuntimeError as error:
        assert str(error) == "The Algorithm class method perform_process() must be overridden by a derived class"
    else:
        assert result is not None


def test_entrypoint_handle_result():
    """Tests entrypoint's handle_result function both by passing in empty parameters and by passing in a file path
    to check for a result"""
    def delete_txt_file():
        if os.path.isfile("data/entrypoint_handle_result.txt"):
            os.remove("data/entrypoint_handle_result.txt")
    entry = entrypoint.__internal__()
    assert entry.handle_result({}) == {}
    assert entry.handle_result({}, "", "") == {}
    assert entry.handle_result({}, 'print') == {}
    delete_txt_file()
    result1 = entry.handle_result({}, 'file', 'data/entrypoint_handle_result.txt')
    assert result1 == json.load(open("data/entrypoint_handle_result.txt"))
    delete_txt_file()
    result2 = entry.handle_result({}, 'all', 'data/entrypoint_handle_result.txt')
    assert result2 == json.load(open("data/entrypoint_handle_result.txt"))


def test_entrypoint_add_parameters():
    """Tests entrypoint's add_parameters function by passing in empty parameters"""
    parser = argparse.ArgumentParser()
    entrypoint.add_parameters(parser, algorithm.Algorithm(), environment.Environment(configuration.Configuration()))
    assert str(parser.parse_args()) == "Namespace(debug=30, file_list=[], info=30, metadata=None," \
                                       " result='all', working_space=None)"


def test_entrypoint_do_work():
    """Tests entrypoint's do_work function by passing in empty parameters"""
    parser = argparse.ArgumentParser()
    try:
        result = entrypoint.do_work(parser, configuration.Configuration(), algorithm.Algorithm())
    except RuntimeError as error:
        assert str(error) == "The Algorithm class method perform_process() must be overridden by a derived class"
    else:
        assert result == {}
