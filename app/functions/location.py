import re
import sys
import requests
import numpy as np
import pandas as pd
from time import sleep
from pathlib import Path
from typing import Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

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
        try:
            df_exists = pd.read_csv(my_file, on_bad_lines="skip", engine="python")
        except Exception:
            df_exists = pd.read_csv(my_file, on_bad_lines="skip")

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
    df_input = new_file.copy()
    df_new = pd.read_csv(stored_file, on_bad_lines="skip", engine="python")

    # ensure Location column exists in cache
    if "Location" not in df_new.columns:
        df_new["Location"] = ""

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
    df_input = df_input[df_input['Country'] == "United States"].copy()

    # append states to the location name
    df_input.loc[:, 'State'] = df_input['State'].apply(lambda x : states.get(x, ""))
    df_input.loc[:, 'Location'] = df_input['City'] + ", " + df_input['State']

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
    cached_locations = pd.read_csv(stored_file, on_bad_lines="skip", engine="python")

    if "Location" not in cached_locations.columns:
        cached_locations["Location"] = ""

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
    new_file = new_file.copy()
    new_file.loc[:, 'State'] = new_file['State'].apply(lambda x : states.get(x, ""))
    new_file.loc[:, 'Location'] = new_file['City'] + ", " + new_file['State']

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

def run(
    input_file: str,
    progress: Optional[Callable[[int, int], None]] = None,
    status: Optional[Callable[[str], None]] = None,
    stored_file: Optional[str] = None,
):
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
    if stored_file is None:
        # default to app/data cache
        stored_file = str(Path(__file__).resolve().parents[1] / "data" / "RiverKeeper_Donors_Unique_Locations.csv")

    # first validate files, if successful, will return the read in csv values
    res, missing_cols = validate(new_file)

    # validation logic
    if (type(res) != type(pd.DataFrame())):
        print("The provided input file is not valid, as it lacks the following columns:" + " ".join(missing_cols))
        return
    
    # generate a list of locations not found and update them
    addressList = generate_queries(stored_file, res)
    if addressList != None:
        run_queries(addressList, stored_file, progress=progress, status=status)

    # now add the updated locations to the input file
    final_df = merge(stored_file, res)

    # return the final dataframe
    return final_df

def run_queries(addressList: list, filename: str, progress: Optional[Callable[[int, int], None]] = None, status: Optional[Callable[[str], None]] = None) -> None:
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
    if not addressList:
        return

    total = len(addressList)
    lock = Lock()
    progress_count = 0
    results = []

    def process(address: str):
        nonlocal results
        query = address.replace(",", "").replace(" ", "+")
        url = f"https://photon.komoot.io/api/?q={query}"

        try:
            response = requests.get(url, timeout=10)
        except Exception:
            print("Request failed for", query)
            return None

        sleep(np.random.randint(1, 3))

        if response.status_code != 200:
            print(f"{query} did not yield any results (status {response.status_code}).")
            return None

        result = response.json().get("features", [])
        if result == []:
            print(query + " did not yield any results.")
            return None

        final_address = disambiguate_address(result[0]['properties'], address)
        df_tmp = pd.DataFrame(data=np.array(final_address).T, columns=['Location', 'Country', 'City', 'Borough', 'County'])
        df_tmp['Country'] = df_tmp['Country'].map(lambda x : x.upper())
        print(query + " has been processed.")
        return df_tmp

    with ThreadPoolExecutor(max_workers=min(8, total)) as executor:
        future_map = {executor.submit(process, addr): addr for addr in addressList}
        for fut in as_completed(future_map):
            df_tmp = fut.result()
            if df_tmp is not None:
                results.append(df_tmp)
            with lock:
                progress_count += 1
                if progress:
                    progress(progress_count, total)
                if status and progress_count % 5 == 0:
                    status(f"Geocoded {progress_count} of {total} locations...")

    df_forcsv = pd.concat(results, ignore_index=True) if results else pd.DataFrame()
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
    data = pd.read_csv(filename, on_bad_lines="skip", engine="python")

    if "Location" not in data.columns:
        data["Location"] = ""

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
