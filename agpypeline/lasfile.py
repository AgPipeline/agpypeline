"""Functions for handling LAS,LAZ files
"""

import json
import os
from typing import Optional
import logging
import subprocess
from osgeo import ogr

from agpypeline import geometries


def clip_las(las_path: str, clip_tuple: tuple, out_path: str) -> None:
    """Clip LAS file to polygon.
    Arguments:
      las_path: path to point cloud file
      clip_tuple: tuple containing (minX, maxX, minY, maxY) of clip bounds
      out_path: output file to write
    Notes:
        The clip_tuple is assumed to be in the correct coordinate system for the point cloud file
    """
    bounds_str = "([%s, %s], [%s, %s])" % (clip_tuple[0], clip_tuple[1], clip_tuple[2], clip_tuple[3])

    pdal_dtm = out_path.replace(".las", "_dtm.json")
    with open(pdal_dtm, 'w', encoding='utf-8') as dtm:
        dtm_data = """{
            "pipeline": [
                "%s",
                {
                    "type": "filters.crop",
                    "bounds": "%s"
                },
                {
                    "type": "writers.las",
                    "filename": "%s"
                }
            ]
        }""" % (las_path, bounds_str, out_path)
        logging.debug("Writing dtm file contents: %s", str(dtm_data))
        dtm.write(dtm_data)

    cmd = 'pdal pipeline "%s"' % pdal_dtm
    logging.debug("Running pipeline command: %s", cmd)
    subprocess.call([cmd], shell=True)
    os.remove(pdal_dtm)


def get_las_epsg(file_path: str, json_result: dict = None) -> Optional[str]:
    """Returns the found EPSG code from the LAS header
    Arguments:
        file_path: the path to the file from which to extract the epsg
        json_result: the json from calling pdal info on a .las file
    Return:
        Returns the SRID as a string if found, None is returned otherwise
    """
    epsg = None
    try:
        if json_result is not None:
            keys = list(json_result['stats']['bbox'].keys())
        else:
            stats = subprocess.run(['pdal', 'info', file_path], stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE, check=True)
            stats_json = json.loads(stats.stdout.decode())
            keys = list(stats_json['stats']['bbox'].keys())
        for key in keys:
            if 'EPSG' in key:
                epsg = key.split(':')[1]
    except Exception as ex:
        logging.debug("Unable to find EPSG in LAS file header")
        logging.debug("    exception caught: %s", str(ex))

    return epsg


def get_las_extents(file_path: str, default_epsg: int = None) -> Optional[str]:
    """Calculate the extent of the given las file and return as GeoJSON.
    Arguments:
        file_path: path to the file from which to load the bounds
        default_epsg: the default EPSG to assume if a file has a boundary but not a coordinate system
    Return:
        Returns the JSON representing the image boundary, or None if the
        bounds could not be loaded
    Notes:
        If a file doesn't have a coordinate system and a default epsg is specified, the
        return JSON will use the default_epsg.
        If a file doesn't have a coordinate system and there isn't a default epsg specified, the boundary
        of the image is not returned (None) and a warning is logged.
    """
    # Get the bounds and the EPSG code
    stats = subprocess.run(['pdal', 'info', file_path], stderr=subprocess.PIPE,
                           stdout=subprocess.PIPE, check=True)
    json_result = json.loads(stats.stdout.decode())
    bounds = json_result['stats']['bbox']['native']['bbox']
    epsg = get_las_epsg(file_path, json_result)
    if epsg is None:
        if default_epsg is not None:
            epsg = default_epsg
        else:
            logging.warning("Unable to find EPSG and not default is specified for file '%s'", file_path)
            return None

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(bounds['minx'], bounds['maxy'])  # Upper left
    ring.AddPoint(bounds['maxx'], bounds['maxy'])  # Upper right
    ring.AddPoint(bounds['maxx'], bounds['miny'])  # lower right
    ring.AddPoint(bounds['minx'], bounds['miny'])  # lower left
    ring.AddPoint(bounds['minx'], bounds['maxy'])  # Closing the polygon

    poly = geometries.polygon_from_ring(ring, int(epsg))
    if poly:
        return geometries.geometry_to_geojson(poly)

    logging.error('Failed to create bounding polygon with EPSG %s from las file "%s"', str(epsg), file_path)
    return None
