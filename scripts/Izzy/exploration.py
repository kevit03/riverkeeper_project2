import pandas as pd
import numpy as np

df = pd.read_csv("scripts/Izzy/cleaned.csv")

#print(len(df["account_id"].unique()))
#print(len(df))

#cities = pd.Series(df["city"].value_counts())
#print(cities[cities<10])
#print(list(cities.index))
#print(df[df["city"]=="Carmel"])


# when messing with the data i noticed:
    # some of the city names with "on Hudson" have "-" in between the words and some don't
    # "New York City" vs "New York"
    # and casing is not 100% uniform, some are all upper
# none of the ids are repeated...
    