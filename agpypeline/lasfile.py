"""Functions for handling LAS,LAZ files
"""

import re
from typing import Optional
import logging
from osgeo import ogr
from osgeo import osr
import liblas

import agpypeline.geometries as geometries


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

    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    ref_sys = osr.SpatialReference()
    if ref_sys.ImportFromEPSG(int(epsg)) == ogr.OGRERR_NONE:
        poly.AssignSpatialReference(ref_sys)
        return geometries.geometry_to_geojson(poly)

    logging.error("Failed to import EPSG %s for las file %s", str(epsg), file_path)
    return None
