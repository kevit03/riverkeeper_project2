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

with open(filename, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        entry = {key: row.get(key, "") for key in fields}
        entry["Latitude"] = None
        entry["Longitude"] = None
        records.append(entry)


# Geocode
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
geocode_records(records, limit=8000, delay=0.2)


# Count donors
counts = defaultdict(int)
for rec in records:
    lat = rec["Latitude"]
    lon = rec["Longitude"]
    if lat is not None and lon is not None:
        counts[(lat, lon)] += 1


# Map
m = folium.Map(location=[40.7128, -74.0060], zoom_start=5)


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


# REAL markers with encoded donor labels in class name
for (lat, lon), num in counts.items():
    folium.Marker(
        location=[lat, lon],
        popup=f"{num} donors here",
        icon=folium.Icon(color="blue", icon="info-sign", prefix="fa", class_name=f"donor-{num}")
    ).add_to(cluster_group)


# Heatmap
heat_points = [[lat, lon, num] for (lat, lon), num in counts.items()]
HeatMap(heat_points, radius=20, blur=15).add_to(m)


m.save("scripts/Kevin/donor_map.html")
print("Saved map to scripts/Kevin/donor_map.html")
