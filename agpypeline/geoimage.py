import json
import numpy as np
import os
import re
import subprocess

from typing import Optional

import yaml
from numpy import nan

from osgeo import gdal
from osgeo import ogr
from osgeo import osr
import logging

import liblas


def calculate_centroid_from_wkt(wkt):
    """Given WKT, return lat/lon of centroid.
    wkt -- string
    returns:
        Tuple of (lat, lon) representing centroid
    """

    loc_geom = ogr.CreateGeometryFromWkt(wkt)
    return (
        loc_geom.Centroid().GetX(),
        loc_geom.Centroid().GetY()
    )


def calculate_overlap_percent(check_bounds: str, bounding_box: str) -> float:
    """Calculates and returns the percentage overlap between the two boundaries.
       The calculation determines the overlap shape between the two parameters and
       then calculates the percentage by dividing the overlap area by the bounding
       box area, and returns that value.
    Args:
        check_bounds: GeoJSON of boundary to check
        bounding_box: GeoJSON of boundary to check against
    Return:
        The calculated overlap percent (0.0 - 1.0) or 0.0 if there is no overlap.
        If an exception is detected, a warning message is logged and 0.0 is returned.
    """
    try:
        check_poly = ogr.CreateGeometryFromJson(str(check_bounds))
        bbox_poly = ogr.CreateGeometryFromJson(str(bounding_box))

        if check_poly and bbox_poly:
            intersection = bbox_poly.Intersection(check_poly)
            if intersection:
                return intersection.Area() / check_poly.Area()
    except Exception as ex:
        logging.warning("Exception caught while calculating shape overlap: %s", str(ex))

    return 0.0


def clip_raster(rast_path, bounds, out_path=None, nodata=-9999, compress=False):
    """Clip raster to polygon.
    Args:
      rast_path (str): path to raster file
      bounds (tuple): (min_y, max_y, min_x, max_x)
      out_path: if provided, where to save as output file
      nodata: the no data value
    Returns: (numpy array, GeoTransform)
    Notes: Oddly, the "features path" can be either a filename
      OR a geojson string. GDAL seems to figure it out and do
      the right thing.
      From http://karthur.org/2015/clipping-rasters-in-python.html
    """

    if not out_path:
        out_path = "temp.tif"

    # Clip raster to GDAL and read it to numpy array
    coords = "%s %s %s %s" % (bounds[2], bounds[1], bounds[3], bounds[0])
    if compress:
        cmd = 'gdal_translate -projwin %s "%s" "%s"' % (coords, rast_path, out_path)
    else:
        cmd = 'gdal_translate -co COMPRESS=LZW -projwin %s "%s" "%s"' % (coords, rast_path, out_path)
    subprocess.call(cmd, shell=True, stdout=open(os.devnull, 'wb'))
    out_px = np.array(gdal.Open(out_path).ReadAsArray())

    if np.count_nonzero(out_px) > 0:
        if out_path == "temp.tif":
            os.remove(out_path)
        return out_px
    else:
        os.remove(out_path)
        return None


def clip_raster_intersection(file_path: str, file_bounds: str, plot_bounds: str, out_file: str) -> Optional[int]:
    """Clips the raster to the intersection of the file bounds and plot bounds
    Arguments:
        file_path: the path to the source file
        file_bounds: the geometric boundary of the source file as JSON
        plot_bounds: the geometric boundary of the plot to clip to as JSON
        out_file: the path to store the clipped image
    Return:
        The number of pixels in the new image, or None if no pixels were saved
    Notes:
        Assumes the boundaries are in the same coordinate system
    Exceptions:
        Raises RuntimeError if the polygons are invalid
    """
    logging.debug("Clip to intersect of plot boundary: File: '%s' '%s' Plot: '%s'", file_path, str(file_bounds),
                  str(plot_bounds))
    try:
        file_poly = ogr.CreateGeometryFromJson(str(file_bounds))
        plot_poly = ogr.CreateGeometryFromJson(str(plot_bounds))

        if not file_poly or not plot_poly:
            logging.error("Invalid polygon specified for clip_raster_intersection: File: '%s' plot: '%s'",
                          str(file_bounds), str(plot_bounds))
            raise RuntimeError("One or more invalid polygons specified when clipping raster")

        intersection = file_poly.Intersection(plot_poly)
        if not intersection or not intersection.Area():
            logging.info("File does not intersect plot boundary: %s", file_path)
            return None

        # Make sure we pass a multipolygon down to the tuple converter
        if intersection.GetGeometryName().startswith('MULTI'):
            multi_polygon = intersection
        else:
            multi_polygon = ogr.Geometry(ogr.wkbMultiPolygon)
            multi_polygon.AddGeometry(intersection)

        # Proceed to clip to the intersection
        tuples = geojson_to_tuples(geometry_to_geojson(multi_polygon))
        return clip_raster(file_path, tuples, out_path=out_file, compress=True)

    except Exception as ex:
        logging.exception("Exception caught while clipping image to plot intersection")
        raise ex


def convert_geometry(geometry, new_spatialreference):
    """Converts the geometry to the new spatial reference if possible
    geometry - The geometry to transform
    new_spatialreference - The spatial reference to change to
    Returns:
        The transformed geometry or the original geometry. If either the
        new Spatial Reference parameter is None, or the geometry doesn't
        have a spatial reference, then the original geometry is returned.
    """
    if not new_spatialreference or not geometry:
        return geometry

    return_geometry = geometry
    try:
        geom_sr = geometry.GetSpatialReference()
        if geom_sr and not new_spatialreference.IsSame(geom_sr):
            transform = osr.CreateCoordinateTransformation(geom_sr, new_spatialreference)
            new_geom = geometry.Clone()
            if new_geom:
                new_geom.Transform(transform)
                return_geometry = new_geom
    except Exception as ex:
        logging.warning("Exception caught while transforming geometries: " + str(ex))
        logging.warning("    Returning original geometry")

    return return_geometry


def find_plots_intersect_boundingbox(bounding_box, all_plots, fullmac=True):
    """Take a list of plots from BETY and return only those overlapping bounding box.
    fullmac -- only include full plots (omit KSU, omit E W partial plots)
    """
    bbox_poly = ogr.CreateGeometryFromJson(str(bounding_box))
    bb_sr = bbox_poly.GetSpatialReference()
    intersecting_plots = dict()

    for plotname in all_plots:
        if fullmac and (plotname.find("KSU") > -1 or plotname.endswith(" E") or plotname.endswith(" W")):
            continue

        bounds = all_plots[plotname]

        yaml_bounds = yaml.safe_load(bounds)
        current_poly = ogr.CreateGeometryFromJson(json.dumps(yaml_bounds))

        # Check for a need to convert coordinate systems
        check_poly = current_poly
        if bb_sr:
            poly_sr = current_poly.GetSpatialReference()
            if poly_sr and not bb_sr.IsSame(poly_sr):
                # We need to convert to the same coordinate system before an intersection
                check_poly = convert_geometry(current_poly, bb_sr)
                transform = osr.CreateCoordinateTransformation(poly_sr, bb_sr)
                new_poly = current_poly.Clone()
                if new_poly:
                    new_poly.Transform(transform)
                    check_poly = new_poly

        intersection_with_bounding_box = bbox_poly.Intersection(check_poly)

        if intersection_with_bounding_box is not None:
            intersection = json.loads(intersection_with_bounding_box.ExportToJson())
            if 'coordinates' in intersection and len(intersection['coordinates']) > 0:
                intersecting_plots[plotname] = bounds

    return intersecting_plots


def geojson_to_tuples(bounding_box: str) -> tuple:
    """Returns the bounds of the shape
    Arguments:
        bounding_box: the JSON of the geometry
    Return:
        A tuple containing the bounds in (min Y, max Y, min X, max X) order
    """
    yaml_geom = yaml.safe_load(bounding_box)
    current_geom = ogr.CreateGeometryFromJson(json.dumps(yaml_geom))
    current_env = current_geom.GetEnvelope()

    return current_env[2], current_env[3], current_env[0], current_env[1]


def geometry_to_geojson(geom, alt_coord_type=None, alt_coord_code=None):
    """Converts a geometry to geojson.
    Args:
        geom(ogr geometry): The geometry to convert to JSON
        alt_coord_type(str): the alternate geographic coordinate system type if geometry doesn't have one defined
        alt_coord_code(str): the alternate geographic coordinate system associated with the type
    Returns:
        The geojson string for the geometry
    Note:
        If the geometry doesn't have a spatial reference associated with it, both the default
        coordinate system type and code must be specified for a coordinate system to be assigned to
        the returning JSON. The original geometry is left unaltered.
    """
    ref_sys = geom.GetSpatialReference()
    geom_json = json.loads(geom.ExportToJson())
    if not ref_sys:
        if alt_coord_type and alt_coord_code:
            # Coming from BETYdb without a coordinate system we assume EPSG:4326
            geom_json['crs'] = {'type': str(alt_coord_type), 'properties': {'code': str(alt_coord_code)}}
    else:
        geom_json['crs'] = {
            'type': ref_sys.GetAttrValue("AUTHORITY", 0),
            'properties': {
                'code': ref_sys.GetAttrValue("AUTHORITY", 1)
            }
        }

    return json.dumps(geom_json)


def get_epsg(filename):
    """Returns the EPSG of the georeferenced image file
    Args:
        filename(str): path of the file to retrieve the EPSG code from
    Return:
        Returns the found EPSG code, or None if it's not found or an error ocurred
    """
    logger = logging.getLogger(__name__)

    try:
        src = gdal.Open(filename)

        proj = osr.SpatialReference(wkt=src.GetProjection())

        return proj.GetAttrValue('AUTHORITY', 1)
    # pylint: disable=broad-except
    except Exception as ex:
        logger.warn("[get_epsg] Exception caught: %s", str(ex))
    # pylint: enable=broad-except

    return None


def get_image_bounds_json(file_path: str, default_epsg: int = None) -> Optional[str]:
    """Loads the boundaries of the image file and returns the GeoJSON
       representing the bounds (including EPSG code)
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
    # Get the bounds (if they exist)
    bounds = image_get_geobounds(file_path)
    if bounds[0] == np.nan:
        return None

    epsg = get_epsg(file_path)
    if epsg is None:
        if default_epsg:
            epsg = default_epsg
        else:
            logging.warning("Files does not have a coordinate system defined and no default was specified: '%s'",
                            file_path)
            return None

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(bounds[2], bounds[1])  # Upper left
    ring.AddPoint(bounds[3], bounds[1])  # Upper right
    ring.AddPoint(bounds[3], bounds[0])  # lower right
    ring.AddPoint(bounds[2], bounds[0])  # lower left
    ring.AddPoint(bounds[2], bounds[1])  # Closing the polygon

    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    ref_sys = osr.SpatialReference()
    if ref_sys.ImportFromEPSG(int(epsg)) == ogr.OGRERR_NONE:
        poly.AssignSpatialReference(ref_sys)
        return geometry_to_geojson(poly)

    logging.error("Failed to import EPSG %s for image file %s", str(epsg), file_path)
    return None


def get_image_file_epsg(source_path: str) -> str:
    """Returns the EPSG of the georeferenced image file
    Arguments:
        source_path: the path to the image to load the EPSG code from
    Return:
        Returns the EPSG code loaded from the file. None is returned if there is a problem or the file
        doesn't have an EPSG code
    """
    # pylint: disable=no-self-use
    try:
        src = gdal.Open(source_path)

        proj = osr.SpatialReference(wkt=src.GetProjection())

        return proj.GetAttrValue('AUTHORITY', 1)
    except Exception as ex:
        logging.debug("[get_image_file_epsg] Exception caught: %s", str(ex))

    return None


def get_image_file_geobounds(source_path: str) -> list:
    """Uses gdal functionality to retrieve rectilinear boundaries from the file
    Args:
        source_path(str): path of the file to get the boundaries from
    Returns:
        The upper-left and calculated lower-right boundaries of the image in a list upon success.
        The values are returned in following order: min_y, max_y, min_x, max_x. A list of numpy.nan
        is returned if the boundaries can't be determined
    """
    # pylint: disable=no-self-use
    try:
        src = gdal.Open(source_path)
        ulx, xres, _, uly, _, yres = src.GetGeoTransform()
        lrx = ulx + (src.RasterXSize * xres)
        lry = uly + (src.RasterYSize * yres)

        min_y = min(uly, lry)
        max_y = max(uly, lry)
        min_x = min(ulx, lrx)
        max_x = max(ulx, lrx)

        return [min_y, max_y, min_x, max_x]
    except Exception as ex:
        logging.debug("[get_image_file_geobounds] Exception caught: %s", str(ex))

    return [nan, nan, nan, nan]


def get_las_epsg_from_header(header: liblas.header.Header) -> str:
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
        return geometry_to_geojson(poly)

    logging.error("Failed to import EPSG %s for las file %s", str(epsg), file_path)
    return None


def image_get_geobounds(filename):
    """Uses gdal functionality to retrieve recilinear boundaries from the file
    Args:
        filename(str): path of the file to get the boundaries from
    Returns:
        The upper-left and calculated lower-right boundaries of the image in a list upon success.
        The values are returned in following order: min_y, max_y, min_x, max_x. A list of numpy.nan
        is returned if the boundaries can't be determined
    """
    logger = logging.getLogger(__name__)

    try:
        src = gdal.Open(filename)
        ulx, xres, _, uly, _, yres = src.GetGeoTransform()
        lrx = ulx + (src.RasterXSize * xres)
        lry = uly + (src.RasterYSize * yres)

        min_y = min(uly, lry)
        max_y = max(uly, lry)
        min_x = min(ulx, lrx)
        max_x = max(ulx, lrx)

        return [min_y, max_y, min_x, max_x]
    # pylint: disable=broad-except
    except Exception as ex:
        logger.info("[image_get_geobounds] Exception caught: %s", str(ex))
    # pylint: enable=broad-except

    return [nan, nan, nan, nan]


def geometry_to_geojson(geom, alt_coord_type=None, alt_coord_code=None):
    """Converts a geometry to geojson.
    Args:
        geom(ogr geometry): The geometry to convert to JSON
        alt_coord_type(str): the alternate geographic coordinate system type if geometry doesn't have one defined
        alt_coord_code(str): the alternate geographic coordinate system associated with the type
    Returns:
        The geojson string for the geometry
    Note:
        If the geometry doesn't have a spatial reference associated with it, both the default
        coordinate system type and code must be specified for a coordinate system to be assigned to
        the returning JSON. The original geometry is left unaltered.
    """
    ref_sys = geom.GetSpatialReference()
    geom_json = json.loads(geom.ExportToJson())
    if not ref_sys:
        if alt_coord_type and alt_coord_code:
            # Coming from BETYdb without a coordinate system we assume EPSG:4326
            geom_json['crs'] = {'type': str(alt_coord_type), 'properties': {'code': str(alt_coord_code)}}
    else:
        geom_json['crs'] = {
            'type': ref_sys.GetAttrValue("AUTHORITY", 0),
            'properties': {
                'code': ref_sys.GetAttrValue("AUTHORITY", 1)
            }
        }

    return json.dumps(geom_json)