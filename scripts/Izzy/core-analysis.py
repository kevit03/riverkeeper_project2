import pandas as pd
import numpy as np
from decimal import Decimal, getcontext
from scipy import stats
import calendar

getcontext().prec = 32

df = pd.read_csv("scripts/Izzy/cleaned.csv")

# total amount of donations
# using decimal module to make sure amount of cents is precise
donations_precise = [Decimal(str(df.loc[row]["total_gifts_amount"])) for row in df.index]
donation_total = np.sum(donations_precise)
print(f"Total Donations: ${donation_total:,f}")

# average donation 
donation_avg = np.mean(donations_precise)
print(f"Average Donation: ${donation_avg:,.2f}")

# median donation
# computing since average is likely skewed by large donations
donation_med = np.median(donations_precise)
print(f"Median Donation: ${donation_med:,.2f}")

# mode donation
donation_mode = df["total_gifts_amount"].value_counts().index[0]
print(f"Modal Donation: ${donation_mode:,.2f}")

# unique donors
unique_donors = len(df["account_id"].unique())
print(f"Unique Donors: {unique_donors:,d}")

# categorizing donors
# using categories based on riverkeeper's website:
    # donors of $20 or more receive email newsletters, invitations, etc.
    # donors of $50 or more receive the "opportunity to vote on [the] Board of Directors at an annual Membership meeting"
    # donors of $250 or more "are listed in [the] annual Impact Report"
df.loc[(df["total_gifts_amount"] < 20), "category"] = "under 20"
df.loc[(df["total_gifts_amount"] >= 20) & (df["total_gifts_amount"] < 50), "category"] = "20+"
df.loc[(df["total_gifts_amount"] >= 50) & (df["total_gifts_amount"] < 250), "category"] = "50+"
df.loc[df["total_gifts_amount"] >= 250, "category"] = "250+"
print("\nDonor Categories:")
for category, count in df["category"].value_counts().items():
    print(f"{category}: {count:,d}")

# top donors
top_donors = df["total_gifts_amount"].sort_values(ascending=False)[:10]
print("\nTop Donors:")
for index, amt in top_donors.items():
    id = df.loc[index]["account_id"]
    print(f"{id}: ${amt:,.2f}")

# grouping by month/year
df["last_gift_date"] = pd.to_datetime(df["last_gift_date"])

# getting counts per month, changing index to month names
month_counts = df["last_gift_date"].dt.month.value_counts().sort_index()
month_counts.index = calendar.month_abbr[1:]

# printing month, counts, and total amount of donations in that month
# sorted by number of donations
print("\nDonations per Month:")
for month, count in month_counts.sort_values(ascending=False).items():
    month_index = list(calendar.month_abbr).index(month)
    amt = sum(df["total_gifts_amount"][df["last_gift_date"].dt.month==month_index])
    print(f"{month}: {count:,d} (${amt:,.2f})")

# getting counts per year, printing year, counts, and total amount of donations in that year
# sorted by number of donations
year_counts = df["last_gift_date"].dt.year.value_counts().sort_values(ascending=False)
print("\nDonations per Year:")
for year, count in year_counts.items():
    amt = sum(df["total_gifts_amount"][df["last_gift_date"].dt.year==year])
    print(f"{year}: {count:,d} (${amt:,.2f})")