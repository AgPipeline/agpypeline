"""Contains geometry functions for translating between representations and coordinate systems
"""

import json
import logging
from typing import Optional
import osgeo
import yaml
from osgeo import ogr
from osgeo import osr


def calculate_centroid_from_wkt(wkt: str) -> tuple:
    """Given WKT, return lat/lon of centroid.
    Arguments:
        wkt: Well Known Text (WKT) format of geometry
    returns:
        Tuple of (lat, lon) representing centroid of the geometry
    """

    # Convert to geometry instance
    loc_geom = ogr.CreateGeometryFromWkt(wkt)
    return loc_geom.Centroid().GetX(), loc_geom.Centroid().GetY()


def calculate_overlap_percent(check_bounds: str, bounding_box: str) -> float:
    """Calculates and returns the percentage overlap between the two boundaries.
       The calculation determines the overlap shape between the two parameters and
       then calculates the percentage by dividing the overlap area by the bounding
       box area, and returns that value.
    Arguments:
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


def convert_geometry(geometry: ogr.Geometry, new_spatialreference: osr.SpatialReference) -> ogr.Geometry:
    """Converts the geometry to the new spatial reference if possible
    Arguments:
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
        if int(osgeo.__version__[0]) >= 3:
            # GDAL 3 changes axis order: https://github.com/OSGeo/gdal/issues/1546
            # pylint: disable=no-member
            geom_sr.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)
        if geom_sr and not new_spatialreference.IsSame(geom_sr):
            transform = osr.CreateCoordinateTransformation(geom_sr, new_spatialreference)
            new_geom = geometry.Clone()
            if new_geom:
                new_geom.Transform(transform)
                return_geometry = new_geom
    except Exception as ex:
        logging.warning("Exception caught while transforming geometries: %s", str(ex))
        logging.warning("    Returning original geometry")

    return return_geometry


def geojson_to_tuples(bounding_box: str) -> tuple:
    """Returns the bounds of the shape
    Arguments:
        bounding_box: the GeoJSON of the geometry
    Return:
        A tuple containing the bounds in (min Y, max Y, min X, max X) order
    """
    yaml_geom = yaml.safe_load(bounding_box)
    current_geom = ogr.CreateGeometryFromJson(json.dumps(yaml_geom))
    return geometry_to_tuples(current_geom)


def geometry_to_tuples(geom: ogr.Geometry) -> tuple:
    """Returns the bounds of the shape
    Arguments:
        geom: the geometry to return the bounds of
    Return:
        A tuple containing the bounds in (min Y, max Y, min X, max X) order
    """
    current_env = geom.GetEnvelope()

    return current_env[2], current_env[3], current_env[0], current_env[1]


def geometry_to_geojson(geom: ogr.Geometry, alt_coord_type: str = None, alt_coord_code: str = None) -> str:
    """Converts a geometry to geojson.
    Args:
        geom: The geometry to convert to JSON
        alt_coord_type: the alternate geographic coordinate system type if geometry doesn't have one defined
        alt_coord_code: the alternate geographic coordinate system associated with the type
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
            # No coordinate system, use what was passed in
            geom_json['crs'] = {'type': str(alt_coord_type), 'properties': {'code': str(alt_coord_code)}}
    else:
        # Use the existing coordinate system to inform the GeoJSON
        geom_json['crs'] = {
            'type': ref_sys.GetAttrValue("AUTHORITY", 0),
            'properties': {
                'code': ref_sys.GetAttrValue("AUTHORITY", 1)
            }
        }
    return json.dumps(geom_json)


def polygon_from_ring(ring: ogr.Geometry, epsg: int = None) -> Optional[ogr.Geometry]:
    """Creates a polygon from the linear ring geometry passed in
    Arguments:
        ring: the linear ring to create the polygon with
        epsg: the EPSG code to assign to the polygon
    Return:
        The created polygon, or None if an EPSG code is specified and can't be loaded
    Exceptions:
        Raises a RuntimeError if a SRID is specified but can't be loaded
    """
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    ref_sys = osr.SpatialReference()
    if epsg is not None:
        if ref_sys.ImportFromEPSG(int(epsg)) == ogr.OGRERR_NONE:
            poly.AssignSpatialReference(ref_sys)
        else:
            return None
    return poly
