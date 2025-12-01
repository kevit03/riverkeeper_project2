import re
import sys
import requests
import numpy as np
import pandas as pd
from time import sleep
from pathlib import Path

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
    This function exports the given address to a csv file.
    WARNING: if 'filename' exists, then the new locations will be appended to the end of this '.csv' file permanently

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

    # concatenate the two dataframes
    df = pd.concat([df, df_exists], ignore_index=True)

    # drop columns that contain the name "Unnamed"
    for column in df.columns:
        if re.search("Unnamed", column) != None:
            df = df.drop(columns=column)

    # formatting filename properly
    if (filename[len(filename)-4 : len(filename)] != ".csv"):
        filename += ".csv"
    
    # export
    df.to_csv(filename)

def generate_queries(stored_file: str, new_file: pd.DataFrame) -> list:
    '''
    A function that reads in an existing '.csv' file, compares its entries to the new file given to it,
    and returns a list containing entries that exist in the new_file but NOT the stored_file.
    The stored file must contain columns labeled 'country', 'city', and 'state'
    
    Args:
        stored_file (str): a string representing where the stored file exists. This is the file that "stores" new entries into it (the OUTPUT file). 
        new_file (pd.DataFrame): contains the data that existed within the INPUT file 

    Returns:
        list: a list containing unique entries existing in the new_file and not the stored_file. If none exist, [] will be returned.
    '''
    # read files
    df_stored = new_file
    df_new = pd.read_csv(stored_file)

    # check 
    if (len(df_stored) == 0):
        print("Your storage file is empty! Cannot generate queries.")
        return
    
    # dictionary to hold states
    states = {"NY": "New York", "AL": "Alabama", "AK": "Alaska", "AZ": " Arizona", "AR": "Arkansas", "ID": "Idaho",
            "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida",
            "KY": "Kentucky", "OH": "Ohio", "LA": "Louisiana", "OK": "Oklahoma", "ME": "Maine", "OR": "Oregon",
            "MD": "Maryland", "PA": "Pennsylvania", "MA": "Massachussets", "PR": "Puerto Rico", "MI": "Michigan",
            "RI": "Rhode Island", "MN": "Minnesota", "SC": "South Carolina", "MS": "Mississippi", "SD": "South Dakota",
            "MO": "Missouri", "TN": "Tennessee", "MT": "Montana", "TX": "Texas", "NE": "Nebraska", "GA": "Georgia", 
            "NV": "Nevada", "UT": "Utah", "GU": "Guam", "NH": "New Hampshire", "VT": "Vermont", "HI": "Hawaii",
            "NJ": "New Jersey", "VA": "Virginia", "NM": "New Mexico", "IL": "Illinois", "WA": "Washington",
            "IN": "Indiana", "NC": "North Carolina", "WV": "West Virginia", "IA": "Iowa", "ND": "North Dakota",
            "WI": "Wisconsin", "KS": "Kansas", "WY": "Wyoming"}

    # filter by country
    df_stored = df_stored[df_stored['country'] == "United States"]

    # append states to the location name
    df_stored['state'] = df_stored['state'].apply(lambda x : states.get(x, ""))
    df_stored['location'] = df_stored['city'] + ", " + df_stored['state']

    # now create the set of new locations
    stored_set = set(df_stored['location'].value_counts().index.to_numpy())

    # format the new file properly and also generate the set 
    new_set = set(df_new['location'])

    # generate unique list
    toRet = list(stored_set - new_set)
    if len(toRet) == 0:
        print("There are no unique locations inside the storage file that don't already exist in your new file!")
        return

    # return new locations
    return toRet

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
    queried = 1

    # initialize the pandas DataFrame
    df_forcsv = pd.DataFrame()

    # iterate over each query
    for address in addressList:
        # rate limit on the 100th query
        if (queried % 5 == 0):
            sleep(10)
        
        # format query for ease
        query = address
        query = query.replace(",", "").replace(" ", "+")

        print(query)

        # hard-coded URL template to access Photon's API
        URL = f"https://photon.komoot.io/api/?q={query}"

        print(URL)

        # this is to ensure the program doesn't crash in case of a Time Out errors
        try:
            # try fetching!
            response = requests.get(URL)
        except:
            # if we get a TimeOut request, break out of the loop
            print("To abide by Photon's request, currently unable to generate ALL the current queries. Please rerun this program after a couple of minutes. Current progress has been saved!")
            break

        # sleep to rate limit
        sleep(np.random.randint(1, 5))

        # successful response indicates 200
        if response.status_code == 200:
            # our address will be located under the property of 'features'
            # since this returns a list, we want to grab the most relevant list of attributes which would be the first one
            # relevant attributes will then be stored under the proprties field
            # to confirm this you can try following the link yourself
            result = response.json().get("features", [])

            # check if somehow the given address did not yield anything
            if result == []:
                print(query + " did not yield any results.")
                continue;
            
            # otherwise continue processing
            final_address = disambiguate_address(result[0]['properties'], address);
            print(result[0]["properties"])
    
            # format a temporary dataframe with new data
            df_tmp = pd.DataFrame(data=np.array(final_address).T, columns=['location', 'country', 'city', 'borough', 'county'])
            df_tmp['country'] = df_tmp['country'].map(lambda x : x.upper())
            
            # verbose commenting
            print(query + " has been processed.")

            # concatenation logic
            if (len(df_forcsv) == 0):
                df_forcsv = df_tmp.copy(deep=True)
            else:
                df_forcsv = pd.concat([df_forcsv, df_tmp], ignore_index=True)

        # increment the number of queries by 1
        queried = queried + 1;
    
    # export all the queries into the selected '.csv' file
    export(df_forcsv, filename)

def validate(filename: str) -> pd.DataFrame:
    '''
    A function that verifies that the input file contains the proper column names

    Args:
        filename (str): path to the file
    
    Returns:
        pd.DataFrame: the proper file in the form specified if the file fails verification, None will be returned
    '''
    # temp vars
    column_names = ["account_id", "city", "state", "country", "total_gifts_amount", "last_gift_date", "gifts_past_18m"]
    column_names_2 = ["Account ID", "City" ,"State", "Country", "Total Gifts (All Time)", "Last Gift Date", "Number of Gifts Past 18 Months"]
    missing_cols = []
    
    # read file
    data = pd.read_csv(filename)

    # check each column
    for i in range(len(column_names)):
        # if the column doesn't exist in the dataframe
        if column_names[i] not in data.columns and column_names_2[i] not in data.columns:
            # add the columns to missing
            missing_cols.append(column_names[i])
    
    # validation logic
    if (len(missing_cols) != 0):
        # return None and the missing columns otherwise
        return None, missing_cols
    else:
        # return the dataframe if verification has succeeded
        return data, missing_cols

def merge(new_file: str, stored_file: pd.DataFrame) -> list:
    '''
    A function that merges the location data and returns a new csv

    Args:
        new_file (str): the output file
        stored_file (pd.DataFrame): the data containing the input file

    Returns:
        None, directly creates the csv file immediately
    '''
    # generate file and create temporary column
    cached_locations = pd.read_csv(new_file)

    # dictionary to hold states
    states = {"NY": "New York", "AL": "Alabama", "AK": "Alaska", "AZ": " Arizona", "AR": "Arkansas", "ID": "Idaho",
            "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida",
            "KY": "Kentucky", "OH": "Ohio", "LA": "Louisiana", "OK": "Oklahoma", "ME": "Maine", "OR": "Oregon",
            "MD": "Maryland", "PA": "Pennsylvania", "MA": "Massachussets", "PR": "Puerto Rico", "MI": "Michigan",
            "RI": "Rhode Island", "MN": "Minnesota", "SC": "South Carolina", "MS": "Mississippi", "SD": "South Dakota",
            "MO": "Missouri", "TN": "Tennessee", "MT": "Montana", "TX": "Texas", "NE": "Nebraska", "GA": "Georgia", 
            "NV": "Nevada", "UT": "Utah", "GU": "Guam", "NH": "New Hampshire", "VT": "Vermont", "HI": "Hawaii",
            "NJ": "New Jersey", "VA": "Virginia", "NM": "New Mexico", "IL": "Illinois", "WA": "Washington",
            "IN": "Indiana", "NC": "North Carolina", "WV": "West Virginia", "IA": "Iowa", "ND": "North Dakota",
            "WI": "Wisconsin", "KS": "Kansas", "WY": "Wyoming"}

    # append states to the location name
    stored_file['state'] = stored_file['state'].apply(lambda x : states.get(x, ""))
    stored_file['location'] = stored_file['city'] + ", " + stored_file['state']

    # perform merge operation
    stored_file = stored_file.merge(cached_locations, how='left', on='location')

    # reformat columns properly
    for column in stored_file.columns:
        if re.search("Unnamed", column) != None or column in ["country_y", "city_y", "location"]:
            stored_file = stored_file.drop(columns=column)
        elif column in ["city_x", "country_x"]:
            stored_file = stored_file.rename(columns={column: column[:-2]}) 

    # reorder columns
    stored_file = stored_file.iloc[:, [0, 1, 10, 9, 2, 5, 3, 4, 6, 7, 8]]    

    # export
    stored_file.to_csv("Biokind_Donor_Information.csv", index=False)

def main():
    # check for usage
    if len(sys.argv) != 3:
        print("This is not how you use the program!")
        print("Usage: python location.py <input_file> <output_file>")

    # hard-coded paths:
    # "../../data/Riverkeeper_Donors_for_NYU_Biokind_Project-10.22.25.csv" for input
    # "RiverKeeper_Donors_Unique_Locations.csv" for output

    stored_file = sys.argv[1] # input file
    new_file = sys.argv[2] # output file

    # first validate files
    res, missing_cols = validate(stored_file)

    # validation logic
    if (type(res) != type(pd.DataFrame())):
        print("The provided input file is not valid, as it lacks the following columns:" + " ".join(missing_cols))

    # generate a list of locations not found and update them
    addressList = generate_queries(new_file, res)
    if addressList != None:
        run_queries(addressList, new_file)

    # now add the updated locations to the input file
    merge(new_file, res)

if (__name__ == "__main__"):
    main()
