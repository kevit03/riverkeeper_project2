import numpy as np
import pandas as pd
from core_analysis import *

df = pd.read_csv("data/merged_dataset.csv")
df["last_gift_date"] = pd.to_datetime(df["last_gift_date"])

#print(stats_by_state(df), "\n")
#print(stats_by_city(df).head(20))

# getting stats for donors without a city or state
country_only = df[df["city"].isnull() & (df["state"].isnull()) & df["country"].notnull()]
print("\ndonations without city and state:")
print("number of donors:", unique_donors(country_only))
print("total donations:", total_donations(country_only))
print("donations in past 18 months:", num_donations_past_18m(country_only))

# getting stats for donors without any location
no_loc = df[df["city"].isnull() & (df["state"].isnull()) & df["country"].isnull()]
print("\ndonations without any location info:")
print("number of donors:", unique_donors(no_loc))
print("total donations:", total_donations(no_loc))
print("donations in past 18 months:", num_donations_past_18m(no_loc))
