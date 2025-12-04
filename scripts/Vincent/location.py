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
    
    city = []
    district = []
    county = []
    country_code = []
    location_ref = [location_name]

    # City / locality handling
    if address.get("type") in ["city", "locality", "town", "village"]:
        city.append(address.get("name", " "))
    elif "city" in address:
        city.append(address["city"])
    elif "locality" in address:
        city.append(address["locality"])
    else:
        city.append(" ")

    # District (borough)
    if address.get("type") == "district":
        district.append(address.get("name", " "))
    elif "district" in address:
        district.append(address["district"])
    else:
        district.append(" ")

    # County
    if address.get("type") == "county":
        county.append(address.get("name", " "))
    elif "county" in address:
        county.append(address["county"])
    else:
        county.append(" ")

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
    df_input = new_file
    df_new = pd.read_csv(stored_file)

    # check 
    if (len(df_input) == 0):
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

    # filter by the US only
    df_input = df_input[df_input['Country'] == "United States"]

    # append states to the location name
    df_input['State'] = df_input['State'].apply(lambda x : states.get(x, ""))
    df_input['Location'] = df_input['City'] + ", " + df_input['State']

    # now create the set of new locations
    stored_set = set(df_input['Location'].value_counts().index.to_numpy())

    # format the new file properly and also generate the set 
    new_set = set(df_new['Location'])

    # generate unique list
    toRet = list(stored_set - new_set)
    if len(toRet) == 0:
        print("There are no unique locations inside the storage file that don't already exist in your new file!")
        return

    # return new locations
    return toRet

def merge(stored_file: str, new_file: pd.DataFrame) -> list:
    '''
    A function that merges the location data and returns a new csv

    Args:
        stored_file (str): the '.csv' file containing the cached locations
        new_file (pd.DataFrame): the data from the input file

    Returns:
        None, directly creates the csv file immediately
    '''
    # generate file and create temporary column
    cached_locations = pd.read_csv(stored_file)

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
    new_file['State'] = new_file['State'].apply(lambda x : states.get(x, ""))
    new_file['Location'] = new_file['City'] + ", " + new_file['State']

    # perform merge operation
    new_file = new_file.merge(cached_locations, how='left', on='Location')

    # reformat columns properly
    for column in new_file.columns:
        if re.search("Unnamed", column) != None or column in ["Country_y", "City_y", "Location"]:
            new_file = new_file.drop(columns=column)
        elif column in ["City_x", "Country_x"]:
            new_file = new_file.rename(columns={column: column[:-2]}) 

    # reorder columns
    new_file = new_file.iloc[:, [0, 1, 10, 9, 2, 5, 3, 4, 6, 7, 8]]    

    # return the file
    return new_file

def run(input_file: str):
    '''
    Run the program

    Args:
        input_file (str): path to the input file

    Returns:
        pd.DataFrame: the merged dataframe
    '''
    # hard-coded paths:
    # "../../data/Riverkeeper_Donors_for_NYU_Biokind_Project-10.22.25.csv" for input
    # "RiverKeeper_Donors_Unique_Locations.csv" for output

    new_file = input_file # input file
    stored_file = "../../data/RiverKeeper_Donors_Unique_Locations.csv" # output file

    # first validate files, if successful, will return the read in csv values
    res, missing_cols = validate(new_file)

    # validation logic
    if (type(res) != type(pd.DataFrame())):
        print("The provided input file is not valid, as it lacks the following columns:" + " ".join(missing_cols))
        return
    
    # generate a list of locations not found and update them
    addressList = generate_queries(stored_file, res)
    if addressList != None:
        run_queries(addressList, stored_file)

    # now add the updated locations to the input file
    final_df = merge(stored_file, res)

    # return the final dataframe
    return final_df

def run_queries(addressList: list, filename: str) -> None:
    ''' 
    A function that runs queries on the list of addresses, compiles them into a pandas DataFrame and exports them to a new csv. 
    In order to abide by Photon's policies and API usage, these requests are severely rate limited at one request every 3 seconds.
    If the number of queries passed exceeds 100, every 100th query will wait an extra 10 seconds.

    Args:
        addressList (list): list of addresses to run queries on
        filename (str): a string containing the path to the '.csv' file that contains previously cached locations

    Returns:
        None: does not return anything
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

        # print query
        print(query)

        # hard-coded URL template to access Photon's API
        URL = f"https://photon.komoot.io/api/?q={query}"

        # decoding
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
            df_tmp = pd.DataFrame(data=np.array(final_address).T, columns=['Location', 'Country', 'City', 'Borough', 'County'])
            df_tmp['Country'] = df_tmp['Country'].map(lambda x : x.upper())
            
            # verbose commenting
            print(query + " has been processed.")

            # concatenation logic
            if (len(df_forcsv) == 0):
                df_forcsv = df_tmp.copy(deep=True)
            else:
                df_forcsv = pd.concat([df_forcsv, df_tmp], ignore_index=True)

        # increment the number of queries by 1
        queried = queried + 1;
    
    # export all the queries into the cached locations to store them
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
    column_names = ["Account ID", "City" ,"State", "Country", "Total Gifts (All Time)", "Last Gift Date", "Number of Gifts Past 18 Months"]
    missing_cols = []
    
    # make sure the path file exists
    my_file = Path(filename)
    if not my_file.is_file():
        print("The input file does not exist. Please try again.")
        sys.exit(1)

    # read file
    data = pd.read_csv(filename)

    # check each column
    for i in range(len(column_names)):
        # if the column doesn't exist in the dataframe
        if column_names[i] not in data.columns:
            # add the columns to missing
            missing_cols.append(column_names[i])
    
    # validation logic
    if (len(missing_cols) != 0):
        # return None and the missing columns otherwise
        return None, missing_cols
    else:
        # return the dataframe if verification has succeeded
        return data, missing_cols