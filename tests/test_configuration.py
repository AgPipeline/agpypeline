#!/usr/bin/env python3
"""
Purpose: Unit testing for basic_configuration.py
Author : Chris Schnaufer <schnaufer@arizona.edu>
Notes:
    This file assumes it's in a subfolder off the main folder
"""
import os

from agpypeline import configuration

TEST_FILES = ['agpypeline/configuration.py']


def test_exists():
    """Tests whether all necessary files are accessible"""
    for file in TEST_FILES:
        assert os.path.isfile(file)


def test_configuration():
    """Tests agpypeline's configuration.Configuration() class by initializing configuration.Configuration() and
     checking to make sure that all necessary parameters are contained"""
    config = configuration.Configuration()
    for entry in ['transformer_version', 'transformer_description', 'transformer_name', 'transformer_sensor',
                  'transformer_type', 'author_name', 'author_email', 'contributors', 'repository']:
        assert hasattr(config, entry)
        if entry == 'contributors':
            assert not getattr(config, entry)
        else:
            assert getattr(config, entry) is None
