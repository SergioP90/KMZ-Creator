# Module in charge of transforming coordinates between different CRS systems, usually to WGS84 (EPSG:4326) (Google Earth's coordinate system)

from pyproj import Proj, Transformer, CRS
from src.exceptions import TranslationError


def transform_coordinates(x, y, utm_zone_label, datum="WGS84"):
    """
    Transforms UTM coordinates to latitude/longitude using pyproj.
    
    Parameters:
        x (float): UTM easting
        y (float): UTM northing
        utm_zone_label (str): UTM zone (e.g., "30T", "33N")
        datum (str): Datum name, default "WGS84"; can use "ETRS89" for Spain
        
    Returns:
        (longitude, latitude) in decimal degrees
    """
    try:
        # Extract zone number and letter
        zone_number = int(''.join(filter(str.isdigit, utm_zone_label)))
        zone_letter = ''.join(filter(str.isalpha, utm_zone_label)).upper()
        
        # Determine hemisphere from zone letter
        hemisphere = 'north' if zone_letter >= 'N' else 'south'
        
        # Determine EPSG code for UTM based on datum and hemisphere
        # Universal fallback to WGS84 UTM EPSG codes
        if datum.upper() == "ETRS89":
            # Spain local zones 28–31 use EPSG:25828–25831
            if 28 <= zone_number <= 31:
                utm_epsg = 25800 + zone_number
            else:
                # fallback: same as WGS84 for other zones
                utm_epsg = 32600 + zone_number if hemisphere == 'north' else 32700 + zone_number
        else:
            # WGS84
            utm_epsg = 32600 + zone_number if hemisphere == 'north' else 32700 + zone_number

        # Create transformer
        transformer = Transformer.from_crs(f"EPSG:{utm_epsg}", "EPSG:4326", always_xy=True)

        # Transform coordinates
        lon, lat = transformer.transform(x, y)
        return lon, lat

    except Exception as e:
        raise TranslationError(f"Error transforming coordinates: {e}")
        