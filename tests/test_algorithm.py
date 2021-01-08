#!/usr/bin/env python3
"""
Purpose: Unit testing for basic_algorithm.py
Author : Chris Schnaufer <schnaufer@arizona.edu>
Notes:
    This file assumes it's in a subfolder off the main folder
"""
import os

from agpypeline import algorithm, configuration, environment

TEST_FILES = ['agpypeline/algorithm.py', 'agpypeline/configuration.py',
              'agpypeline/environment.py']


def test_exists():
    """Tests whether all necessary files are accessible"""
    for file in TEST_FILES:
        assert os.path.isfile(file)


def test_algorithm():
    """Tests initializing the algorithm.Algorithm() class within agpypeline and performing a process with default
    parameters """
    alg = algorithm.Algorithm()
    try:
        res = alg.perform_process(environment.Environment(configuration.Configuration()), {}, {}, [])
    except RuntimeError as error:
        assert str(error) == "The Algorithm class method perform_process() must be overridden by a derived class"
    else:
        assert isinstance(res, dict)
