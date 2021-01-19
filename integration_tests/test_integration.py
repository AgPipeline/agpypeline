#!/usr/bin/env python3
"""Suite of Integration tests
"""
import os
import random
import string

from subprocess import getstatusoutput

SOURCE_FILE = 'integration_tests/basic_algorithm.py'
SOURCE_PATH = os.path.abspath(os.path.join('', SOURCE_FILE))

TESTING_JSON_FILE_PATH = os.path.realpath('./integration_tests/integration_tests_data')
META = os.path.abspath(os.path.join(TESTING_JSON_FILE_PATH, 'meta.yaml'))
INPUT1 = os.path.abspath(os.path.join(TESTING_JSON_FILE_PATH, 'rgb_17_7_W.tif'))


def random_string():
    """generate a random string"""
    k = random.randint(5, 10)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=k))


def test_no_metadata_or_files():
    """Test the output when no metadata or file_list is included on the command line"""
    ret_val, out = getstatusoutput(f'{SOURCE_PATH}')
    assert int(ret_val) == 0 and int(out) == 0


def test_metadata_no_files():
    """Test the output when no file_list is included on the command line"""
    ret_val, out = getstatusoutput(f'{SOURCE_PATH} --metadata {META}')
    assert int(ret_val) == 0 and int(out) == 0


def test_metadata_and_files():
    """Tests the output when valid arguments are entered on the command line"""
    out_dir = random_string()
    os.makedirs(out_dir)
    # This ought not be necessary as the program *should*
    # create it; for now, we'll create the output dir.

    ret_val, out = getstatusoutput(f'{SOURCE_PATH} {INPUT1} --working_space {out_dir} --metadata {META}')
    assert int(ret_val) == 0 and int(out) == 0
