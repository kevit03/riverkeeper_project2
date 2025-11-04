import pandas as pd
import numpy as np
from core_analysis import *

df1 = pd.read_csv("scripts/Izzy/donors.csv")
df2 = pd.read_csv("scripts/Izzy/donors2.csv")

df1["last_gift_date"] = pd.to_datetime(df1["last_gift_date"])
df2["last_gift_date"] = pd.to_datetime(df2["last_gift_date"])
df2.rename(columns={'total_gifts_all_time': 'total_gifts_amount', "number_of_gifts_past_18_months": "gifts_past_18m"}, inplace=True)

# looking at how many account ids appear in both datasets vs how many are unique to each dataset
print(len(shared_values(df1, df2, "account_id")))
print("\ndonors unique to first dataset:")
print(unique_values(df1, df2, "account_id")[0])
print("\ndonors unique to second dataset:")
print(unique_values(df1, df2, "account_id")[1])

# merging datasets
df = merge_on_id(df1, df2)

# splitting data into active and inactive donors
active = df[df["gifts_past_18m"] > 0]
inactive = df[df["gifts_past_18m"] == 0 | np.isnan(df["gifts_past_18m"])]

# unique active and inactive donors in each table
print("active donors:", unique_donors(active))
print("inactive donors:", unique_donors(inactive))

# top active and inactive donors
print("\ntop active donors:\n", top_donors(active, 10))
print("\ntop inactive donors:\n", top_donors(inactive, 10))

# donors who have made the most donations in the past 18 months
print("\nmost frequent active donors:\n", most_frequent_donors(active, 10))

# number of donations that have been made in the past 18 months
print("\nnumber of donations in the past 18 months:", num_donations_past_18m(active))

print(month_counts(df))
print(year_counts(df))

# new data per year table
data_per_year = data_per_year(df)
print(data_per_year)

df.to_csv("data/merged_dataset.csv", index=False)