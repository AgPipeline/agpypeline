"""Functions for handling LAS,LAZ files
"""

import re
import os
from typing import Optional
import logging
import subprocess
from osgeo import ogr
import liblas

import agpypeline.geometries as geometries


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
    with open(pdal_dtm, 'w') as dtm:
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


def get_las_epsg_from_header(header: liblas.header.Header) -> Optional[str]:
    """Returns the found EPSG code from the LAS header
    Arguments:
        header: the loaded LAS header to find the SRID in
    Return:
        Returns the SRID as a string if found, None is returned otherwise
    """
    epsg = None
    search_terms_ordered = ['DATUM', 'AUTHORITY', '"EPSG"', ',']
    try:
        # Get the WKT from the header, find the DATUM, then finally the EPSG code
        srs = header.get_srs()
        wkt = srs.get_wkt().decode('UTF-8')
        idx = -1
        for term in search_terms_ordered:
            idx = wkt.find(term)
            if idx < 0:
                break
        if idx >= 0:
            epsg = re.search(r'\d+', wkt[idx:])[0]
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
    las_info = liblas.file.File(file_path, mode='r')
    min_bound = las_info.header.min
    max_bound = las_info.header.max
    epsg = get_las_epsg_from_header(las_info.header)
    if epsg is None:
        if default_epsg is not None:
            epsg = default_epsg
        else:
            logging.warning("Unable to find EPSG and not default is specified for file '%s'", file_path)
            return None

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(min_bound[1], min_bound[0])  # Upper left
    ring.AddPoint(min_bound[1], max_bound[0])  # Upper right
    ring.AddPoint(max_bound[1], max_bound[0])  # lower right
    ring.AddPoint(max_bound[1], min_bound[0])  # lower left
    ring.AddPoint(min_bound[1], min_bound[0])  # Closing the polygon

    poly = geometries.polygon_from_ring(ring, int(epsg))
    if poly:
        return geometries.geometry_to_geojson(poly)

    logging.error('Failed to create bounding polygon with EPSG %s from las file "%s"', str(epsg), file_path)
    return None
