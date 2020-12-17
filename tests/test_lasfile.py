#!/usr/bin/env python3
"""
Purpose: Unit testing for geometries.py
Author : Chris Schnaufer <schnaufer@arizona.edu>
Notes:
    This file assumes it's in a subfolder off the main folder
"""
# import json
# import subprocess
#
# from liblas import file
# from liblas.header import Header
#
# from agpypeline import lasfile


# def test_get_las_epsg_from_header():  # More tests might be needed in order to know if it works for a non-null epsg
#     """Tests get_las_epsg_from_header by creating a blank Header object"""
#     header = Header()
#     assert lasfile.get_las_epsg_from_header(header) is None
#     las_file = file.File("images/points.las", mode='r')
#     header_from_file = las_file.header
#     result = lasfile.get_las_epsg_from_header(header_from_file)
#     assert result is None


# bounds_str = "([%s, %s], [%s, %s])" % (366400, 367000, 3967000, 3967500)
# bounds_str = "([%s, %s], [%s, %s], [%s, %s])" % (366400, 367000, 3967000, 3967500, 2617, 2893)
# res = lasfile.clip_las("images/points.las", (366400, 3967000, 367000, 3967500), "images/lasfile_clip_las.las")
# with open(pdal_dtm, 'w') as dtm:
#     dtm_data = """{
#         "pipeline": [
#             {
#                 "type": "readers.las",
#                 "spatialreference": "EPSG:26913",
#                 "filename": "%s"
#             },
#             {
#                 "type": "filters.crop",
#                 "bounds": "%s"
#             },
#             {
#                 "type": "writers.las",
#                 "filename": "%s"
#             }
#         ]
#     }""" % (las_path, bounds_str, out_path)
#     logging.debug("Writing dtm file contents: %s", str(dtm_data))
#     dtm.write(dtm_data)
# cmd = 'pdal pipeline "%s"' % pdal_dtm
# logging.debug("Running pipeline command: %s", cmd)
# os.system(cmd)
# subprocess.call([cmd], shell=True)
# os.remove(pdal_dtm)


# def test_lasfile_clip_las():
#     """A .las file is needed but is not able to be pushed to GitHub because it is too large"""
#     min_x = None
#     max_x = None
#     min_y = None
#     max_y = None
#     lasinfo = subprocess.check_output('lasinfo images/points.las',
#                                       shell=True)
#     lasinfo_decoded = lasinfo.decode("utf-8")
#     split = lasinfo_decoded.splitlines()
#     for line in split:
#         line_modified = " ".join(line.split())
#         line_modified_2 = line_modified.split(" ")
#         if line_modified_2[0] == "Min":
#             min_x = float(line_modified_2[4].replace(",", ""))
#             min_y = float(line_modified_2[5].replace(",", ""))
#         elif line_modified_2[0] == "Max":
#             max_x = float(line_modified_2[4].replace(",", ""))
#             max_y = float(line_modified_2[5].replace(",", ""))
#     clip_min_x = min_x + (max_x - min_x) * 0.25
#     clip_max_x = min_x + (max_x - min_x) * 0.75
#     clip_min_y = min_y + (max_y - min_y) * 0.25
#     clip_max_y = min_y + (max_y - min_y) * 0.75
#     lasfile.clip_las("images/points2.las",
#                      (clip_min_x, clip_max_x, clip_min_y, clip_max_y), "images/clip_las_out.las")
#
#
# def test_get_las_extents():
#     """Get the extents of a LAS file"""
#     check_output = json.load(open("data/lasfile_get_las_extents.json"))
#     result = lasfile.get_las_extents("../points.las", 4326)
#     assert check_output == json.loads(result)
