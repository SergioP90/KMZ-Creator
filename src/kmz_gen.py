import os
import zipfile
from pykml.factory import KML_ElementMaker as KML
from lxml import etree, objectify
from shapely.geometry import Point
from colorama import Fore, Style
from pyproj import Geod


KML_NS = "http://www.opengis.net/kml/2.2"
NS = {"kml": KML_NS}


class KMZManager:
    def __init__(self, file_path=None):
        """
        Initialize the manager. If file_path is provided, open the KMZ.
        Otherwise, create a new KML document in memory.

        Parameters:
            file_path (str): Path to the KMZ file to open or save. If None, starts with an empty KML.

        Returns:
            None
        """
        self.file_path = file_path
        self.kml = KML.kml(KML.Document())

        if file_path and os.path.exists(file_path):
            self._load_kmz(file_path)


    def _load_kmz(self, kmz_path):
        """
        Load KMZ from file_path into memory for editing.
        
        Parameters:
            kmz_path (str): Path to the KMZ file to open.

        Returns:
            None
        """
        with zipfile.ZipFile(kmz_path, 'r') as zf:
            kml_filename = [name for name in zf.namelist() if name.endswith('.kml')][0]
            kml_data = zf.read(kml_filename)

            # Parse and objectify
            root = objectify.fromstring(kml_data)
            self.kml = root

            duplicates = self._check_duplicate_names()
            if duplicates:
                print(f"{Fore.YELLOW}Warning: Duplicate placemark names found: {', '.join(duplicates)}.\nThis will cause issues when updating or deleting points.\nThe modification algorithm will target the first placemark with a matching name.{Style.RESET_ALL}")


    def save(self, file_path=None):
        """
        Save KMZ to disk

        Parameters:
            file_path (str): Path to save the KMZ file. If None, overwrites the original file if opened from one.

        Returns:
            None
        """
        file_path = file_path or self.file_path
        if not file_path:
            raise ValueError("No file path provided to save the KMZ.")

        kml_data = etree.tostring(self.kml, pretty_print=True)
        with zipfile.ZipFile(file_path, 'w') as zf:
            zf.writestr("doc.kml", kml_data)

        self.file_path = file_path


    def add_point(self, name, lon, lat):
        """
        Add a point with the given name and coordinates in lat/lon (WGS84).
        
        Parameters:
            name (str): Name of the placemark
            lon (float): Longitude in decimal degrees
            lat (float): Latitude in decimal degrees

        Returns:
            True if added successfully, False if a point with the same name exists.
        """
        existing_points = self.list_points()
        for pt in existing_points:
            if pt['name'] == name:
                print(f"{Fore.RED}A point with the name '{name}' already exists. Choose a different name.{Style.RESET_ALL}")
                return False

        point = KML.Placemark(
            KML.name(name),
            KML.Point(
                KML.coordinates(f"{lon},{lat}")
            )
        )
        self.kml.Document.append(point)
        return True


    def _ensure_objectified(self):
        """
        Make sure self.kml is an objectified tree (has .pyval / _setText, etc.).
        
        Parameters:
            None

        Returns:
            None
        """
        if not hasattr(self.kml, "tag") or not isinstance(self.kml, objectify.ObjectifiedElement):
            self.kml = objectify.fromstring(etree.tostring(self.kml))


    def list_points(self):
        """
        List all point Placemarks in the KMZ.
        
        Parameters:
            None

        Returns:
            [{'name': str, 'longitude': float, 'latitude': float}, ...]
        """
        self._ensure_objectified()
        points = []
        for pm in self.kml.xpath(".//kml:Placemark", namespaces=NS):
            pt = pm.find(f"{{{KML_NS}}}Point")
            if pt is None:
                continue
            coords_elem = pt.find(f"{{{KML_NS}}}coordinates")
            if coords_elem is None:
                continue
            # Coordinates can be "lon,lat" or "lon,lat,alt". For Point it should be a single tuple.
            raw = getattr(coords_elem, "pyval", None)
            if raw is None:
                raw = (coords_elem.text or "").strip()
            first = raw.strip().split()[0] if raw else ""
            parts = [p for p in first.split(",") if p != ""]
            if len(parts) >= 2:
                name_elem = pm.find(f"{{{KML_NS}}}name")
                name = getattr(name_elem, "pyval", None) if name_elem is not None else None
                points.append({
                    "name": name or "Unnamed",
                    "longitude": float(parts[0]),
                    "latitude": float(parts[1]),
                })
        return points


    def update_point(self, old_name, new_name=None, new_lon=None, new_lat=None):
        """
        Update a point placemark identified by its current name.
        - Rename if new_name is given.
        - Move if both new_lon and new_lat are given.
        Returns True if a placemark was updated, False otherwise.

        Parameters:
            old_name (str): Current name of the placemark to update
            new_name (str): New name to set. If None, name is unchanged.
            new_lon (float): New longitude in decimal degrees. If None, longitude is unchanged.
            new_lat (float): New latitude in decimal degrees. If None, latitude is unchanged.

        Returns:
            True if a placemark was updated, False otherwise.
        """
        self._ensure_objectified()

        for pm in self.kml.xpath(".//kml:Placemark", namespaces=NS):
            name_elem = pm.find(f"{{{KML_NS}}}name")
            current_name = getattr(name_elem, "pyval", None) if name_elem is not None else None
            if current_name == old_name:
                # Rename
                if new_name is not None:
                    # objectify requires _setText for StringElement
                    name_elem._setText(str(new_name))

                # Move (only if both lon/lat provided)
                if new_lon is not None and new_lat is not None:
                    pt = pm.find(f"{{{KML_NS}}}Point")
                    if pt is None:
                        # If it exists but isn't a Point, skip (or create a Point if you prefer)
                        return False
                    coords_elem = pt.find(f"{{{KML_NS}}}coordinates")
                    if coords_elem is None:
                        coords_elem = objectify.Element(f"{{{KML_NS}}}coordinates")
                        pt.append(coords_elem)

                    # Preserve altitude if present
                    raw = getattr(coords_elem, "pyval", None)
                    if raw is None:
                        raw = (coords_elem.text or "").strip()
                    alt = None
                    if raw:
                        first = raw.strip().split()[0]
                        parts = [p for p in first.split(",") if p != ""]
                        if len(parts) >= 3:
                            alt = parts[2]

                    new_txt = f"{new_lon},{new_lat}" + (f",{alt}" if alt is not None else "")
                    coords_elem._setText(new_txt)

                return True
        return False


    def delete_point(self, name):
        """
        Delete the first Placemark whose <name> matches.
        Returns True if deleted, False if not found.

        Parameters:
            name (str): Name of the placemark to delete

        Returns:
            True if deleted, False if not found.
        """
        self._ensure_objectified()

        for pm in self.kml.xpath(".//kml:Placemark", namespaces=NS):
            name_elem = pm.find(f"{{{KML_NS}}}name")
            current_name = getattr(name_elem, "pyval", None) if name_elem is not None else None
            if current_name == name:
                pm.getparent().remove(pm)
                return True
        return False


    def _check_duplicate_names(self):
        """
        Check for duplicate placemark names and return a list of duplicates.
        
        Parameters:
            None

        Returns:
            List of duplicate names (str). Empty if none found.
        """
        points = self.list_points()
        name_count = {}
        for pt in points:
            name = pt['name']
            name_count[name] = name_count.get(name, 0) + 1
        duplicates = [name for name, count in name_count.items() if count > 1]
        return duplicates


    def compute_distances_all(self, datum="WGS84"):
        """
        Compute distances between all points (every pair).
        Returns a list of tuples: (name1, name2, distance_meters)

        Parameters:
            datum (str): Datum to use for distance calculation. Default "WGS84".

        Returns:
            List of tuples: (name1, name2, distance_meters)
        """
        points = self.list_points()
        geod = Geod(ellps=datum)

        distances = []
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                p1, p2 = points[i], points[j]
                _, _, dist = geod.inv(
                    p1['longitude'], p1['latitude'],
                    p2['longitude'], p2['latitude']
                )
                distances.append((p1['name'], p2['name'], dist))
        return distances


    def compute_distances_line(self, datum="WGS84"):
        """
        Compute distances only between consecutive points (a chain/line).
        Returns a list of tuples: (name1, name2, distance_meters)

        Parameters:
            datum (str): Datum to use for distance calculation. Default "WGS84".

        Returns:
            List of tuples: (name1, name2, distance_meters)
        """
        points = self.list_points()
        geod = Geod(ellps=datum)

        distances = []
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            _, _, dist = geod.inv(
                p1['longitude'], p1['latitude'],
                p2['longitude'], p2['latitude']
            )
            distances.append((p1['name'], p2['name'], dist))
        return distances
