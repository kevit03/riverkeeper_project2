import numpy as np
import pandas as pd
from geopy.geocoders import Nominatim
from pathlib import Path
from time import sleep

# OBJECTIVE: Split City columns into Four columns
# 1 Country Code
# 2 City
# 3 Borough
# 4 County

# read in data
df = pd.read_csv("../Izzy/cleaned.csv")

# format to take care of NaNs
df['city'] = df[['city']].fillna("?")
df['state'] = df[['state']].fillna("?")

# new feature creation 
df['location'] = df['city'] + ", " + df['state']

# create a list of unique values so we don't actually go through every possible item
# self-check has shown this array contains 1283 values
item = df['location'].value_counts().index.to_numpy()

# this removes the value of "?, ?" which is generated from both the city and state being empty...
item = np.delete(item, [1])

# function
def geolocate(x, lower, upper, places):
    ''' Create an array that attempts to find specific details about a location such as City, Borough, County
    Args:
        x: the list of locations, should be unique
        lower: the lower range of indexes to find locations of, needed to avoid being ratelimited
        upper: the upper range of indexes to find locations of, difference between upper and lower cannot be greater than 500
        places: a dictionary to store the list of locations
    Returns:
        A dictionary, key is the entry taken from x and value is another dictionary, which contains the relevant address details
    '''
    # constructor set up to use for geocoding
    geolocator = Nominatim(user_agent="tutorial") #EnergyHire    

    # iterate over every row in X
    while lower < upper:
        # if out of bounds, end
        if (lower > len(x)):
            break

        # grab location name
        place = x[lower]

        # get location data
        loc = geolocator.geocode(place, addressdetails=True)

        # the raw property breaks down the address into specific components which we will need
        # the address indexer helps us limit our data down to relevant details
        places[place] = loc.raw['address']
        
        # next row
        lower += 1;
    
        # sleep for tres segundos to avoid timeouts
        sleep(3)

    # return our places
    return places

# create our global variable of places
geoList = {}

# the algorithm cannot handle more than 500 at a time without severely being rate limited
for i in range(3):
    geoList = geolocate(item, i * 500, ((i + 1) * 500) - 1, geoList)

# now that we have our full list of locations
# we can loop through the actual data and start generating columns

# column placeholders
city = []
borough = [] # not consistent in general
county = []
country_code = []

# iterate through the new locations
for item in df['location']:
    # if its an empty location don't fill in anything
    if item == "?, ?":
        city.append(" ")
        borough.append(" ")
        county.append(" ")
        country_code.append(" ")

    # city array
    if 'city' in geoList[item]:
        city.append(geoList[item]['city'])
    elif 'town' in geoList[item]:
        city.append(geoList[item]['town'])
    # if neither key exists for this address, leave it blank
    else:
        city.append(" ")

    # county array
    if 'county' in geoList[item]:
        county.append(geoList[item]['county'])
    # if key doesn't exist for this address, leave it blank
    else:
        county.append(" ")
    
    # country_code array
    if "country_code" in geoList[item]:
        country_code.append(geoList[item]['country_code'])
    # if key doesn't exist for this address, leave it blank
    else:
        country_code.append(" ")

    # borough array
    if 'municipality' in geoList[item]:
        borough.append(geoList[item]['municipality'])
    elif 'suburb' in geoList[item]:
        borough.append(geoList[item]['suburb'])
    # if neither key exists for this address, leave it blank
    else:
        borough.append(" ")

# column assignment
df['borough'] = borough
df['county'] = county
df['country_code'] = country_code
df['city'] = city