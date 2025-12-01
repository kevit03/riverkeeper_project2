import csv
import json
import time
from collections import defaultdict

from geopy.geocoders import Nominatim
import folium
from folium.plugins import MarkerCluster, HeatMap


# Load CSV
filename = "data/Riverkeeper_Donors.csv"
fields = ["City", "State", "Country"]
records = []

def build_map():
    return m


with open(filename, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        entry = {key: row.get(key, "") for key in fields}
        entry["Latitude"] = None
        entry["Longitude"] = None
        records.append(entry)


def is_kansas(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
    except:
        return False

    return (36.99 <= lat <= 40.01) and (-102.06 <= lon <= -94.58)


# Coordinate validator
def is_valid_coordinate(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
    except:
        return False

    if abs(lat) > 90 or abs(lon) > 180:
        return False

    if lat == 0 and lon == 0:
        return False

    return True

    # reject None
    if lat is None or lon is None:
        return False            
    
    # reject strings like "40.8" or "NaN"
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return False

    # reject extreme impossible values
    if abs(lat) > 90 or abs(lon) > 180:
        return False

    # reject (0,0)
    if lat == 0 and lon == 0:
        return False

    return True





# Geocoding
def geocode_records(data, limit=100, delay=0.2, cache_path="scripts/Kevin/geocode_cache.json"):
    try:
        with open(cache_path, "r") as f:
            cache = json.load(f)
    except FileNotFoundError:
        cache = {}

    for entry in data[:limit]:
        query = f"{entry['City']}, {entry['State']}, {entry['Country']}"

        if query in cache:
            entry["Latitude"], entry["Longitude"] = cache[query]
            continue

        try:
            loc = geolocator.geocode(query)
            if loc:
                lat, lon = loc.latitude, loc.longitude
            else:
                lat, lon = None, None
        except Exception:
            lat, lon = None, None

        cache[query] = (lat, lon)
        entry["Latitude"], entry["Longitude"] = lat, lon
        time.sleep(delay)

    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)


geolocator = Nominatim(user_agent="heatmap_script", timeout=10)
geocode_records(records, limit=len(records), delay=0.2)


# Count donors, but skip invalid coordinates
counts = defaultdict(int)
invalid_count = 0
kansas_count = 0

for rec in records:
    lat = rec["Latitude"]
    lon = rec["Longitude"]

    if not is_valid_coordinate(lat, lon):
        invalid_count += 1
        continue

    # NEW: detect Kansas fallback values
    if is_kansas(lat, lon):
        kansas_count += 1
        continue

    counts[(lat, lon)] += 1


# Create map with no infinite horizontal scrolling
m = folium.Map(
    location=[40.7128, -74.0060],
    zoom_start=5,
    max_bounds=True,
    world_copy_jump=False
)


# Sidebar legend for invalid locations
legend_html = f"""
<div style="
    position: fixed; 
    top: 50px; 
    left: 50px; 
    width: 280px; 
    background-color: white;
    border: 2px solid grey; 
    z-index: 9999; 
    padding: 12px;
    font-size: 14px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
">
<b>Unmapped Entries Summary</b><br><br>
Missing geocodes: <span style='color:red;'>{invalid_count + kansas_count}</span><br>
</div>
"""


m.get_root().html.add_child(folium.Element(legend_html))


# Cluster JS using encoded class donor-XX
cluster_js = """
function(cluster) {
    var markers = cluster.getAllChildMarkers();
    var total = 0;

    markers.forEach(function(m) {
        var cls = m.options.icon.options.className;
        var match = cls.match(/donor-(\\d+)/);
        if (match) {
            total += parseInt(match[1]);
        }
    });

    var color = "blue";
    if (total < 11) color = "green";
    else if (total < 51) color = "blue";
    else if (total < 151) color = "orange";
    else color = "red";

    return L.divIcon({
        html: '<div style="background-color:' + color +
              '; border-radius:20px; width:40px; height:40px; display:flex; ' +
              'align-items:center; justify-content:center; color:white; ' +
              'font-weight:bold;">' + total + '</div>',
        className: 'donor-cluster',
        iconSize: new L.Point(40, 40)
    });
}
"""

cluster_group = MarkerCluster(icon_create_function=cluster_js).add_to(m)


# Add real markers
for (lat, lon), num in counts.items():
    folium.Marker(
        location=[lat, lon],
        popup=f"{num} donors here",
        icon=folium.Icon(color="blue", class_name=f"donor-{num}")
    ).add_to(cluster_group)


# Heatmap
heat_points = [[lat, lon, num] for (lat, lon), num in counts.items()]
HeatMap(heat_points, radius=20, blur=15).add_to(m)


# Save output
m.save("scripts/Kevin/donor_map.html")
print("Saved map to scripts/Kevin/donor_map.html")
