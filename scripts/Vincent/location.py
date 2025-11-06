import numpy as np
import pandas as pd
from time import sleep
import requests

def disambiguate_address(address: dict, location_name: str) -> list:
    '''
    A function that takes a JSON object containing an addresses attributes and breaks them into four specific categories: locality, district, city, and country code
    Geographical order from smallest area to largest: locality --> district --> city --> country code

    Args:
        address (dict): a dictionary that contains attributes relating to the specific address
        location_name (str): a string that represents the original location name
    
    Returns:
        list: an array containing the address broken into the 4 aforementioned categories plus the name of the place itself
    '''

    # initialize empty arrays
    city = []
    district = [] 
    county = []
    country_code = []
    location_ref = []

    # location array
    location_ref.append(location_name)

    # input features accordingly
    if address['type'] == 'county':
        county.append(address['name'])
    elif 'county' in address:
        county.append(address['county'])   
    else:
        county.append(" ")

    if address['type'] == 'city':
        city.append(address['name'])
    elif 'city' in address:
        city.append(address['city'])
    else:
        city.append(" ")

    if address['type'] == 'district':
        district.append(address['name'])
    elif 'district' in address:
        district.append(address['district'])
    else:
        district.append(" ")

    if 'countrycode' in address:
        country_code.append(address['countrycode'])
    else:
        country_code.append("US")

    return [location_ref, country_code, city, district, county]

def export(df: pd.DataFrame, filename: str) -> None:
    '''
    This function exports the given address to a csv file. If file exists, data will be appended as long as the formats match.

    Args:
        address (pd.DataFrame): a pandas DataFrame containing all the addresses to export; the elements must be in the order of 'Location' -> 'Country' -> 'City' -> 'Borough' -> 'County
        filename (str): a string containing the name of the csv file you plan to export to

    Returns:
        None: does not return anything.
    '''
    # grab files
    my_file = Path(filename)
    df_exists = pd.DataFrame()

    # check if file exists, if it does read file and combine
    if my_file.is_file():
        df_exists = pd.read_csv(my_file)
        df_exists = df_exists[df.columns]

    df = pd.concat([df, df_exists], ignore_index=True)

    # formatting filename properly
    if (filename[len(filename)-4 : len(filename)] != ".csv"):
        filename += ".csv"
    
    # export
    df.to_csv(filename)

def generate_queries(stored_file: str, new_file) -> list:
    '''
    A function that reads in an existing '.csv' file, compares its entries to the new file given to it,
    and returns a list containing entries that exist in the new_file but NOT the stored_file.
    
    Args:
        stored_file (str): a string representing where the stored file exists. This is the file that "stores" new entries into it. 
        new_file (str): a string representing where the new file exists. This is the file that will be used to generate entries from.

    Returns:
        list: a list containing unique entries existing in the new_file and not the stored_file. If none exist, [] will be returned.
    '''
    # read files
    df_stored = pd.read_csv(stored_file)
    df_new = pd.read_csv(new_file)
    
    # filter by New York entries and generate set of entries from the stored file
    df_stored = df_stored[df_stored['State'] == "NY"]
    stored_set = set(df_stored['City'].value_counts().index.to_numpy())

    # format the new file properly and also generate the set 
    df_new.drop("Unnamed: 0", axis=1, inplace=True)
    new_set = set(df_new['Location'])

    # generate unique list and return
    return list(stored_set - new_set)

def run_queries(addressList: list, filename: str) -> None:
    ''' 
    A function that runs queries on the list of addresses, compiles them into a pandas DataFrame and exports them to a new csv. 
    In order to abide by Photon's policies and API usage, these requests are severely rate limited at one request every 3 seconds.
    If the number of queries passed exceeds 100, every 100th query will wait an extra 10 seconds.

    Args:
        addressList (list): list of addresses to run queries on
        filename (str): a string representing the filename to create the .csv file. If the ".csv" file already exists, the address queries will be appended to the end of the existing ".csv" file.

    Returns:
        None: does not return anything.
    '''
    # counter variable
    queried = 0

    # initialize the pandas DataFrame
    df_forcsv = pd.DataFrame()

    # iterate over each query
    for address in addressList:
        # rate limit on the 100th query
        if (queried % 100 == 0):
            sleep(10)
        
        # append "New York" tag to avoid location ambiguity
        query = address + " new york"
        query = query.replace(" ", "+")

        # hard-coded URL template to access Photon's API
        URL = f"https://photon.komoot.io/api/?q={query}"

        # fetch!
        response = requests.get(URL)

        # sleep to rate limit
        sleep(3)

        # successful response indicates 200
        if response.status_code == 200:
            # our address will be located under the property of 'features'
            # since this returns a list, we want to grab the most relevant list of attributes which would be the first one
            # relevant attributes will then be stored under the proprties field
            # to confirm this you can try following the link yourself
            result = response.json().get("features", [])
            final_address = disambiguate_address(result[0]['properties'], address);
    
            # format a temporary dataframe with new data
            df_tmp = pd.DataFrame(data=np.array(final_address).T, columns=['Location', 'Country', 'City', 'Borough', 'County'])
            df_tmp['Country'] = df_tmp['Country'].map(lambda x : x.upper())

            # concatenation logic
            if (len(df_forcsv) == 0):
                df_forcsv = df_tmp
            else:
                df_forcsv = pd.concat([df_forcsv, df_tmp], ignore_index=True)
        
        # increment the number of queries by 1
        queried = queried + 1;
                
    # export all the queries into the selected '.csv' file
    export(df_forcsv, filename)

def main():
    stored_file = "../../data/Riverkeeper_Donors_for_NYU_Biokind_Project-10.22.25.csv"
    new_file = "RiverKeeper_Donors_Unique_Locations.csv"

    addressList = generate_queries(stored_file, new_file)
    run_queries(addressList, new_file)

if (__name__ == "__main__"):
    main()