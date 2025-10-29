import csv; 
from geopy.geocoders import Nominatim
import time 
import folium
from folium.plugins import FastMarkerCluster
import pandas as pd 


geolocator = Nominatim(user_agent="heatmap_script", timeout = 10)

filename = 'data/Riverkeeper_Donors.csv' 
keys = ["City", "State", "Country",] #keys to extract from the CSV
records = [] #List to hold the extracted records

#Read the CSV and extract the relevant fields "keys" defined above 
with open(filename, 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        record = {key: row.get(key, "") for key in keys}
        record["Latitude"] = None
        record["Longitude"] = None
        records.append(record)


# unused data processing code
# df = pd.DataFrame(records)
# donor_counts = df.groupby("City").size().reset_index(name="Count")


# Geocode the first 'limit' records with a delay between requests   
import json

def geocode_records(records, limit=100, delay=0.2, cache_file="scripts/Kevin/geocode_cache.json"):
    # Try to load existing cache
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
    except FileNotFoundError:
        cache = {}

    for place in records[:limit]:
        query = f"{place['City']}, {place['State']}, {place['Country']}"

        # If already cached, reuse
        if query in cache:
            lat, lon = cache[query]
            place['Latitude'], place['Longitude'] = lat, lon
            continue

        # Otherwise, make a new geocoding call
        try:
            location = geolocator.geocode(query)
            if location:
                lat, lon = location.latitude, location.longitude
                cache[query] = (lat, lon)
                place['Latitude'], place['Longitude'] = lat, lon
            else:
                cache[query] = (None, None)
                place['Latitude'], place['Longitude'] = (None, None)
        except Exception as e:
            print(f"Error geocoding {query}: {e}")
            cache[query] = (None, None)
            place['Latitude'], place['Longitude'] = (None, None)

        time.sleep(delay)

    # Save updated cache to file
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)




geocode_records(records, limit = 1000, delay= .1)
map = folium.Map(location=[40.7128, -74.0060], zoom_start=5) # Centered on New York City

# Prepare data for FastMarkerCluster
latitude = [a['Latitude'] for a in records if a['Latitude'] is not None]
longitude = [a['Longitude'] for a in records if a['Longitude'] is not None]
locations = list(zip(latitude, longitude))

FastMarkerCluster(data=locations).add_to(map)

# Alternative: Add individual circle markers
# for record in records: 
#     coords = (record.get('Latitude'), record.get('Longitude'))
#     if coords[0] is not None and coords[1] is not None:
#         folium.CircleMarker(
#             location=coords,
#             radius=5,
#             popup=f"{record['City']}, {record['State']}",
#             color='blue',
#             fill=True,
#             fill_color='blue'
#         ).add_to(map)

map.save("scripts/Kevin/donor_map.html")
print("Map has been saved to data/donor_map.html")
