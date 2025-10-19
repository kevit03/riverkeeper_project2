import pandas as pd
from decimal import Decimal, getcontext
import calendar

getcontext().prec = 32

df = pd.read_csv("scripts/Izzy/cleaned.csv")
df["last_gift_date"] = pd.to_datetime(df["last_gift_date"]) # transforming last gift date column to datetime

def donations_precise(df: pd.DataFrame) -> pd.Series:
    '''
    converts the dollar amounts to Decimal objects to maintain precision
    '''
    precise = df["total_gifts_amount"].apply(lambda x: Decimal(str(x)))
    return precise

def total_donations(df: pd.DataFrame) -> float:
    '''
    returns the sum of all donations by all donors
    '''
    donation_total = donations_precise(df).sum()
    return round(donation_total, 2)

def avg_total_donation(df: pd.DataFrame) -> float:
    '''
    returns the average total donation amount
    '''
    donation_avg = donations_precise(df).mean()
    return round(donation_avg, 2)

def median_total_donation(df: pd.DataFrame) -> float:
    '''
    returns the median total donation amount
    '''
    donation_median = donations_precise(df).median()
    return round(donation_median, 2)

def modal_total_donation(df: pd.DataFrame) -> float:
    '''
    returns the most common total donation amount
    '''
    donation_mode = donations_precise(df).value_counts().index[0]
    return round(donation_mode, 2)

def unique_donors(df: pd.DataFrame) -> int:
    '''
    returns the number of unique donors
    '''
    return len(df["account_id"].unique())

def categorize_donors(df: pd.DataFrame) -> pd.Series:
    '''
    adds a column to the dataset categorizing donors based on amount
    returns value counts for categories
    categories come from riverkeeper's website: https://engage.riverkeeper.org/give:
        donors of $20 or more receive email newsletters, invitations, etc.
        donors of $50 or more receive the opportunity to vote on the Board of Directors at an annual Membership meeting
        donors of $250 or more are listed in the annual Impact Report
    '''
    df.loc[(df["total_gifts_amount"] < 20), "category"] = "under 20"
    df.loc[(df["total_gifts_amount"] >= 20) & (df["total_gifts_amount"] < 50), "category"] = "20+"
    df.loc[(df["total_gifts_amount"] >= 50) & (df["total_gifts_amount"] < 250), "category"] = "50+"
    df.loc[df["total_gifts_amount"] >= 250, "category"] = "250+"
    return df["category"].value_counts()

def top_donors(df: pd.DataFrame, n: int) -> pd.DataFrame:
    '''
    returns top n donors with account id, total amount, and date of last donation
    '''
    sorted_donations = df.sort_values(by="total_gifts_amount", ascending=False)
    top_donors = sorted_donations[:n]
    return top_donors[["account_id", "total_gifts_amount", "last_gift_date"]]

def month_counts(df: pd.DataFrame) -> pd.Series:
    '''
    returns series with the number of donors who made their last donation in each month
    '''
    month_counts = df["last_gift_date"].dt.month.value_counts().sort_index()
    month_counts.index = calendar.month_abbr[1:]
    return month_counts
    
def year_counts(df: pd.DataFrame) -> pd.Series:
    '''
    returns series with the number of donors who made their last donation in each year
    '''
    year_counts = df["last_gift_date"].dt.year.value_counts().sort_index()
    return year_counts
    
def data_per_year(df: pd.DataFrame) -> pd.DataFrame:
    '''
    returns a dataframe with columns:
        year
        number of donors who last donated in that year
        top donor who last donated in that year
        average total donation amount of those who stopped donating that year
        median total donation amount of those who stopped donating that year
    '''
    res = pd.DataFrame(index=year_counts(df).index)
    res.index.name = "Year"

    res["Count"] = year_counts(df).values
    res["Top Amount"] = df.groupby(df["last_gift_date"].dt.year)["total_gifts_amount"].max()
    res["Average Amount"] = df.groupby(df["last_gift_date"].dt.year)["total_gifts_amount"].mean().round(2)
    res["Median Amount"] = df.groupby(df["last_gift_date"].dt.year)["total_gifts_amount"].median()

    return res

print(data_per_year(df))