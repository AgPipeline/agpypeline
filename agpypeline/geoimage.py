"""Functions for handling geo referenced images
"""

import os
import subprocess
from typing import Callable, Optional
import logging
import numpy as np
import osgeo
from osgeo import gdal
from osgeo import ogr
from osgeo import osr

from agpypeline import geometries

LAT_LON_EPSG_CODE = 4326


def clip_raster(raster_path: str, bounds: tuple, out_path: str = None, compress: bool = True) -> Optional[np.ndarray]:
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
    # pylint: disable=consider-using-with
    subprocess.call(cmd, shell=True, stdout=open(os.devnull, 'wb'))
    out_px = np.array(gdal.Open(out_path).ReadAsArray())

    # If we have any pixels, we consider clipping a success
    if out_px.shape[0] > 0 and out_px.shape[1] > 0:
        if out_path == "temp.tif":
            os.remove(out_path)
        return out_px

    os.remove(out_path)
    return None


def clip_raster_intersection(file_path: str, file_bounds: ogr.Geometry, plot_bounds: ogr.Geometry, out_file: str) ->\
        Optional[int]:
    """Clips the raster to the intersection of the file bounds and plot bounds
    Arguments:
        file_path: the path to the source file
        file_bounds: the geometric boundary of the source file
        plot_bounds: the geometric boundary of the plot to clip to
        out_file: the path to store the clipped image
    Return:
        The number of pixels in the new image, or None if no pixels were saved
    Notes:
        Assumes the boundaries are in the same coordinate system
    Exceptions:
        Raises RuntimeError if the polygons are invalid
    """
    logging.debug("Clip to intersect of plot boundary: File: '%s' '%s' Plot: '%s'", file_path, str(file_bounds), str(plot_bounds))
    try:
        if not file_bounds or not plot_bounds:
            logging.error("Invalid polygon specified for clip_raster_intersection: File: '%s' plot: '%s'",
                          str(file_bounds), str(plot_bounds))
            raise RuntimeError("One or more invalid polygons specified when clipping raster")

        intersection = file_bounds.Intersection(plot_bounds)
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
        tuples = geometries.geometry_to_tuples(multi_polygon)
        return clip_raster(file_path, tuples, out_path=out_file, compress=True)

    except Exception as ex:
        logging.exception("Exception caught while clipping image to plot intersection")
        raise ex


def clip_raster_intersection_json(file_path: str, file_bounds: str, plot_bounds: str, out_file: str) -> Optional[int]:
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

    file_poly = ogr.CreateGeometryFromJson(str(file_bounds))
    plot_poly = ogr.CreateGeometryFromJson(str(plot_bounds))

    if not file_poly or not plot_poly:
        logging.error("Invalid polygon specified for clip_raster_intersection: File: '%s' plot: '%s'",
                      str(file_bounds), str(plot_bounds))
        raise RuntimeError("One or more invalid polygons specified when clipping raster")

    return clip_raster_intersection(file_path, file_poly, plot_poly, out_file)


def common_create_tiff(pixels: np.ndarray, out_path: str, nodata: int = -99, as_float: bool = False,
                       image_md: dict = None, compress: bool = False,
                       raster_update_func: Callable[[osgeo.gdal.Dataset], None] = None) -> None:
    """Common tiff file generating function
    Arguments:
        pixels: numpy array of pixel values.
                    if 2-dimensional array, a single-band GeoTIFF will be created.
                    if 3-dimensional array, a band will be created for each Z dimension.
        out_path: path to GeoTIFF to be created
        nodata: NoDataValue to be assigned to raster bands; set to None to ignore
        as_float: whether to use GDT_Float32 data type instead of GDT_Byte (e.g. for decimal numbers)
        image_md: metadata to save with the geotiff
        compress: compress image pixels (loss less)
        raster_update_func: optional callback function for modifying the raster before it's saved. Called
                before the metadata or pixels are set/saved in the target image.
    """
    dimensions = np.shape(pixels)
    if len(dimensions) == 2:
        nrows, ncols = dimensions
        channels = 1
    else:
        nrows, ncols, channels = dimensions

    # Create output GeoTIFF and set coordinates & projection
    dtype = gdal.GDT_Float32 if as_float else gdal.GDT_Byte

    tiff_options = ['COMPRESS=LZW', 'PREDICTOR=2'] if compress else ['BIGTIFF=IF_NEEDED']
    output_raster = gdal.GetDriverByName('GTiff').Create(out_path, ncols, nrows, channels, dtype, tiff_options)

    if raster_update_func is not None:
        raster_update_func(output_raster)

    output_raster.SetMetadata(image_md)

    if channels in [3, 4]:
        # RGB and RGBA channels
        channel_types = [gdal.GCI_RedBand, gdal.GCI_GreenBand, gdal.GCI_BlueBand, gdal.GCI_AlphaBand]
        for chan in range(channels):
            band = chan + 1
            output_raster.GetRasterBand(band).WriteArray(pixels[:, :, chan].astype('uint8'))
            output_raster.GetRasterBand(band).SetColorInterpretation(channel_types[chan])
            output_raster.GetRasterBand(band).FlushCache()
            if nodata:
                output_raster.GetRasterBand(band).SetNoDataValue(nodata)
    elif channels > 1:
        for chan in range(channels):
            band = chan + 1
            output_raster.GetRasterBand(band).WriteArray(pixels[:, :, chan].astype('uint8'))
            output_raster.GetRasterBand(band).FlushCache()
            if nodata:
                output_raster.GetRasterBand(band).SetNoDataValue(nodata)
    else:
        # single channel image, e.g. temperature
        output_raster.GetRasterBand(1).WriteArray(pixels)
        output_raster.GetRasterBand(1).FlushCache()
        if nodata:
            output_raster.GetRasterBand(1).SetNoDataValue(nodata)


def create_geotiff(pixels: np.ndarray, gps_bounds: tuple, out_path: str, srid: int, nodata: int = -99,
                   as_float: bool = False, image_md: dict = None, compress: bool = False) -> None:
    """Generate output GeoTIFF file given a numpy pixel array and GPS boundary.
    Arguments:
        pixels: numpy array of pixel values.
                    if 2-dimensional array, a single-band GeoTIFF will be created.
                    if 3-dimensional array, a band will be created for each Z dimension.
        gps_bounds: tuple of GeoTIFF coordinates as ( lat (y) min, lat (y) max,
                                                        long (x) min, long (x) max)
        out_path: path to GeoTIFF to be created
        srid: the SRID of the geographic system to assign to the image
        nodata: NoDataValue to be assigned to raster bands; set to None to ignore
        as_float: whether to use GDT_Float32 data type instead of GDT_Byte (e.g. for decimal numbers)
        image_md: metadata to save with the geotiff
        compress: compress image pixels (loss less)
    """
    def set_geotransform(raster: osgeo.gdal.Dataset) -> None:
        """Internal function sets the geotransformation information for the image before it's saved
        Arguments:
            raster: the raster to setup
        """
        geotransform = (
            gps_bounds[2],  # upper-left x
            (gps_bounds[3] - gps_bounds[2]) / float(raster.RasterXSize),  # W-E pixel resolution
            0,  # rotation (0 = North is up)
            gps_bounds[1],  # upper-left y
            0,  # rotation (0 = North is up)
            -((gps_bounds[1] - gps_bounds[0]) / float(raster.RasterYSize))  # N-S pixel resolution
        )

        raster.SetGeoTransform(geotransform)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(int(srid))
        raster.SetProjection(srs.ExportToWkt())

    # Call the common code to create the raster
    common_create_tiff(pixels, out_path, nodata, as_float, image_md, compress, set_geotransform)


def create_tiff(pixels: np.ndarray, out_path: str, nodata: int = -99, as_float: bool = False,
                image_md: dict = None, compress: bool = False) -> None:
    """Generate output GeoTIFF file given a numpy pixel array and GPS boundary.
    Arguments:
        pixels: numpy array of pixel values.
                    if 2-dimensional array, a single-band GeoTIFF will be created.
                    if 3-dimensional array, a band will be created for each Z dimension.
        out_path: path to GeoTIFF to be created
        nodata: NoDataValue to be assigned to raster bands; set to None to ignore
        as_float: whether to use GDT_Float32 data type instead of GDT_Byte (e.g. for decimal numbers)
        image_md: metadata to save with the geotiff
        compress: compress image pixels (loss less)
    """
    common_create_tiff(pixels, out_path, nodata, as_float, image_md, compress)


def get_centroid_latlon(filename: str) -> ogr.Geometry:
    """Returns the bounds and epsg of a geo-referenced image file
    Arguments:
        filename: the path to the file to get the centroid from
    Returns:
        Returns the centroid of the geometry loaded from the file in lat-lon coordinates
        as a result of calling geometries.get_centroid_latlon()
    Exceptions:
        RuntimeError is raised if the image is not a geo referenced image with an EPSG code,
        the EPSG code is not supported, or another problems occurs
    """
    epsg = get_epsg(filename)

    poly = get_image_bounds(filename, epsg)
    if poly is None:
        msg = "File is not a geo-referenced image file: %s" % filename
        logging.error(msg)
        raise RuntimeError(msg)
    if epsg is None:
        msg = "EPSG is not found in image file: '%s'" % filename
        logging.error(msg)
        raise RuntimeError(msg)
    # Convert the polygon to lat-lon
    dest_spatial = osr.SpatialReference()
    if int(osgeo.__version__[0]) >= 3:
        # GDAL 3 changes axis order: https://github.com/OSGeo/gdal/issues/1546
        # pylint: disable=no-member
        dest_spatial.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)

    if dest_spatial.ImportFromEPSG(int(LAT_LON_EPSG_CODE)) != ogr.OGRERR_NONE:
        msg = "Failed to import EPSG %s for conversion to lat-lon" % str(LAT_LON_EPSG_CODE)
        logging.error(msg)
        raise RuntimeError(msg)
    ref_sys = osr.SpatialReference()
    if ref_sys.ImportFromEPSG(int(epsg)) != ogr.OGRERR_NONE:
        msg = "Failed to import EPSG %s for conversion to lat-lon" % str(epsg)
        logging.error(msg)
        raise RuntimeError(msg)
    transform = osr.CoordinateTransformation(ref_sys, dest_spatial)
    new_src = poly.Clone()
    if new_src:
        new_src.Transform(transform)
    else:
        msg = "Failed to transform file polygon to lat-lon %s" % filename
        logging.error(msg)
        raise RuntimeError(msg)
    return new_src.Centroid()


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


def get_image_bounds(file_path: str, default_epsg: int = None) -> Optional[ogr.Geometry]:
    """Loads the boundaries of the image file and returns the geometry representing the bounds
    Arguments:
        file_path: path to the file from which to load the bounds
        default_epsg: the default EPSG to assume if a file has a boundary but not a coordinate system
        as a result of calling geometries.polygon_from_ring
    Return:
        Returns the geometry representing the image boundary, or None if the
        bounds could not be loaded
    Notes:
        If a file doesn't have a coordinate system and a default epsg is specified, the
        return JSON will use the default_epsg.
        If a file doesn't have a coordinate system and there isn't a default epsg specified, the boundary
        of the image is not returned (None) and a warning is logged.
    """
    # Get the bounds (if they exist)
    bounds = image_get_geobounds(file_path)
    if np.nan in bounds:
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
    return geometries.polygon_from_ring(ring, int(epsg))


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
    geom = get_image_bounds(file_path, default_epsg)
    if geom:
        return geometries.geometry_to_geojson(geom)

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
