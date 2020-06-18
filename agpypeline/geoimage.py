"""Functions for handling geo referenced images
"""

import os
import subprocess
from typing import Optional
import logging
import numpy as np

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

import geometries


def clip_raster(raster_path: str, bounds: tuple, out_path: str = None, compress=True) -> Optional[np.ndarray]:
    """Clip raster to polygon
    Arguments:
      raster_path: path to raster file
      bounds: (min_y, max_y, min_x, max_x)
      out_path: if provided, where to save as output file
      compress: set to False to disable compression of resulting image (defaults to True)
    Return:
        A numpy array of image pixels
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
        cmd = 'gdal_translate -projwin %s "%s" "%s"' % (coords, raster_path, out_path)
    else:
        cmd = 'gdal_translate -co COMPRESS=LZW -projwin %s "%s" "%s"' % (coords, raster_path, out_path)
    subprocess.call(cmd, shell=True, stdout=open(os.devnull, 'wb'))
    out_px = np.array(gdal.Open(out_path).ReadAsArray())

    if np.count_nonzero(out_px) > 0:
        if out_path == "temp.tif":
            os.remove(out_path)
        return out_px

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
        tuples = geometries.geojson_to_tuples(geometries.geometry_to_geojson(multi_polygon))
        return clip_raster(file_path, tuples, out_path=out_file, compress=True)

    except Exception:
        logging.exception("Exception caught while clipping image to plot intersection")


def get_epsg(filename: str) -> Optional[str]:
    """Returns the EPSG of the georeferenced image file
    Args:
        filename: path of the file to retrieve the EPSG code from
    Return:
        Returns the found EPSG code, or None if it's not found or an error ocurred
    """
    try:
        src = gdal.Open(filename)

        proj = osr.SpatialReference(wkt=src.GetProjection())

        return proj.GetAttrValue('AUTHORITY', 1)
    except Exception as ex:
        logging.warning("[get_epsg] Exception caught: %s", str(ex))

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
        return geometries.geometry_to_geojson(poly)

    logging.error("Failed to import EPSG %s for image file %s", str(epsg), file_path)
    return None


def image_get_geobounds(source_path: str) -> list:
    """Uses gdal functionality to retrieve rectilinear boundaries from the file
    Args:
        source_path(str): path of the file to get the boundaries from
    Returns:
        The upper-left and calculated lower-right boundaries of the image in a list upon success.
        The values are returned in following order: min_y, max_y, min_x, max_x. A list of numpy.nan
        is returned if the boundaries can't be determined
    """
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
        logging.debug("[image_get_geobounds] Exception caught: %s", str(ex))

    return [np.nan, np.nan, np.nan, np.nan]
