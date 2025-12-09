import pandas as pd
import numpy as np
from decimal import Decimal, getcontext
import calendar

getcontext().prec = 32

def categorize_donors(df: pd.DataFrame) -> pd.DataFrame:
    '''
    adds a column to the dataset categorizing donors based on amount
    returns the new dataframe with that column
    categories come from riverkeeper's website: https://engage.riverkeeper.org/give:
        donors of $20 or more receive email newsletters, invitations, etc.
        donors of $50 or more receive the opportunity to vote on the Board of Directors at an annual Membership meeting
        donors of $250 or more are listed in the annual Impact Report
    '''
    df.loc[(df["Total Gifts (All Time)"] < 20), "Category"] = "under 20"
    df.loc[(df["Total Gifts (All Time)"] >= 20) & (df["Total Gifts (All Time)"] < 50), "Category"] = "20+"
    df.loc[(df["Total Gifts (All Time)"] >= 50) & (df["Total Gifts (All Time)"] < 250), "Category"] = "50+"
    df.loc[df["Total Gifts (All Time)"] >= 250, "Category"] = "250+"
    return df

def clean(df: pd.DataFrame) -> pd.DataFrame:
    '''
    converts numeric data to numeric types and dates to datetime type and adds the category column
    '''
    df = df.copy()
    # ensure required columns exist
    required = [
        "Account ID",
        "Total Gifts (All Time)",
        "Number of Gifts Past 18 Months",
        "Last Gift Date",
        "City",
        "State",
        "Country",
    ]
    for col in required:
        if col not in df.columns:
            df[col] = None
    # strip and clean location fields; drop numeric-only placeholders
    df["City"] = df["City"].apply(lambda x: str(x).strip() if pd.notna(x) else np.nan)
    df["State"] = df["State"].apply(lambda x: str(x).strip() if pd.notna(x) else np.nan)
    df.loc[df["City"].isin(["", "nan", "NaN", "None", "none"]), "City"] = np.nan
    df.loc[df["State"].isin(["", "nan", "NaN", "None", "none"]), "State"] = np.nan
    df.loc[df["City"].str.fullmatch(r"\d+", na=False), "City"] = np.nan
    df.loc[df["State"].str.fullmatch(r"\d+", na=False), "State"] = np.nan
    # drop any city values that contain digits (e.g., stray numeric labels)
    df.loc[df["City"].str.contains(r"\d", na=False), "City"] = np.nan
    df.loc[df["State"].str.contains(r"\d", na=False), "State"] = np.nan

    # ensure strings before string ops
    df["Total Gifts (All Time)"] = (
        df["Total Gifts (All Time)"]
        .astype(str)
        .str.removeprefix("$")
        .str.replace(",", "")
    )
    df["Total Gifts (All Time)"] = pd.to_numeric(df["Total Gifts (All Time)"], errors="coerce")
    df["Number of Gifts Past 18 Months"] = pd.to_numeric(df["Number of Gifts Past 18 Months"], errors="coerce")
    df["Last Gift Date"] = pd.to_datetime(df["Last Gift Date"], errors="coerce")
    return df


# basic stats

def donations_precise(df: pd.DataFrame) -> pd.Series:
    '''
    converts dollar amounts to Decimal objects to maintain precision
    '''
    precise = df["Total Gifts (All Time)"].map(lambda x: Decimal(str(x)))
    return precise

def total_donations(df: pd.DataFrame) -> float:
    donation_total = donations_precise(df).sum()
    return round(donation_total, 2)

def avg_total_donation(df: pd.DataFrame) -> float:
    donation_avg = donations_precise(df).mean()
    return round(donation_avg, 2)

def median_total_donation(df: pd.DataFrame) -> float:
    donation_median = donations_precise(df).median()
    return round(donation_median, 2)

def modal_total_donation(df: pd.DataFrame) -> float:
    donation_mode = donations_precise(df).mode()
    if isinstance(donation_mode, pd.Series) and not donation_mode.empty:
        donation_mode = donation_mode.iloc[0]
    elif isinstance(donation_mode, pd.Series) and donation_mode.empty:
        return 0.0
    return round(donation_mode, 2)

def basic_stats(df: pd.DataFrame) -> pd.DataFrame:
    '''
    returns a dataframe of basic statistics with columns
        number of unique donors,
        total amount donated,
        average total donation,
        median total donation,
        modal total donation,
        number of donations in past 18 months
    '''
    res = pd.DataFrame({
        "Donors" : [df["Account ID"].nunique()],
        "Total Donation Amount" : [f"${total_donations(df):,.2f}"],
        "Average Total Donation" : [f"${avg_total_donation(df):,.2f}"],
        "Median Total Donation" : [f"${median_total_donation(df):,.2f}"],
        "Modal Total Donation" : [f"${modal_total_donation(df):,.2f}"],
        "Gifts in Past 18 Months" : [int(df["Number of Gifts Past 18 Months"].sum())]
    })
    return res

def active_donors(df: pd.DataFrame) -> pd.DataFrame:
    '''
    basic stats for active donors with average number of gifts per donor in the past 18 months
    '''
    active = df[df["Number of Gifts Past 18 Months"] > 0]
    res = basic_stats(active)
    res["Average Gifts Past 18 Months"] = round(active["Number of Gifts Past 18 Months"].mean(), 2)
    res.rename(columns={"Donors": "Active Donors"}, inplace=True)
    return res

def inactive_donors(df: pd.DataFrame) -> pd.DataFrame:
    '''
    basic stats for inactive donors
    '''
    inactive = df[(df["Number of Gifts Past 18 Months"] == 0) | (np.isnan(df["Number of Gifts Past 18 Months"]))]
    res = basic_stats(inactive)
    res.rename(columns={"Donors": "Inactive Donors"}, inplace=True)
    return res

def top_donors(df: pd.DataFrame, n: int) -> pd.DataFrame:
    '''
    returns top n donors with 
        account id,
        city,
        state,
        total amount,
        last gift date,
        donations in past 18 months
    '''
    df = df.replace({"": np.nan, "None": np.nan, "none": np.nan})
    for col in ["Total Gifts (All Time)", "City", "State"]:
        if col not in df.columns:
            df[col] = np.nan
    # drop rows with missing key fields
    df = df.dropna(subset=["Total Gifts (All Time)", "City", "State"])
    sorted_donations = df.copy().sort_values(by="Total Gifts (All Time)", ascending=False)
    sorted_donations["Last Gift Date"] = pd.to_datetime(sorted_donations["Last Gift Date"], errors="coerce")
    sorted_donations["Number of Gifts Past 18 Months"] = pd.to_numeric(sorted_donations["Number of Gifts Past 18 Months"], errors="coerce").fillna(0)
    top_donors = sorted_donations[:n].copy()
    top_donors["Total Gifts (All Time)"] = top_donors["Total Gifts (All Time)"].apply(lambda x: '${:,.2f}'.format(x))
    top_donors["Last Gift Date"] = top_donors["Last Gift Date"].dt.date
    top_donors["Number of Gifts Past 18 Months"] = top_donors["Number of Gifts Past 18 Months"].astype(int)
    top_donors.reset_index(drop=True, inplace=True)
    return top_donors[["Account ID", "City", "State", "Total Gifts (All Time)", "Last Gift Date", "Number of Gifts Past 18 Months"]]

def frequent_donors(df: pd.DataFrame, n: int) -> pd.DataFrame:
    '''
    returns n most frequent donors with 
        account id,
        city,
        state,
        total amount,
        last gift date,
        donations in past 18 months
    '''
    df = df.replace({"": np.nan, "None": np.nan, "none": np.nan})
    for col in ["Number of Gifts Past 18 Months", "City", "State"]:
        if col not in df.columns:
            df[col] = np.nan
    # drop rows with missing key fields
    df = df.dropna(subset=["Number of Gifts Past 18 Months", "City", "State"])
    sorted_donations = df.copy().sort_values(by=["Number of Gifts Past 18 Months", "Total Gifts (All Time)"], ascending=False)
    sorted_donations["Last Gift Date"] = pd.to_datetime(sorted_donations["Last Gift Date"], errors="coerce")
    sorted_donations["Number of Gifts Past 18 Months"] = pd.to_numeric(sorted_donations["Number of Gifts Past 18 Months"], errors="coerce").fillna(0)
    frequent_donors = sorted_donations[:n].copy()
    frequent_donors["Total Gifts (All Time)"] = frequent_donors["Total Gifts (All Time)"].apply(lambda x: '${:,.2f}'.format(x))
    frequent_donors["Last Gift Date"] = frequent_donors["Last Gift Date"].dt.date
    frequent_donors["Number of Gifts Past 18 Months"] = frequent_donors["Number of Gifts Past 18 Months"].astype(int)
    frequent_donors.reset_index(drop=True, inplace=True)
    return frequent_donors[["Account ID", "City", "State", "Total Gifts (All Time)", "Last Gift Date", "Number of Gifts Past 18 Months"]]

# stats by location

def state_donations(df: pd.DataFrame, state: str) -> pd.DataFrame:
    '''
    returns subset of the data with donations in the given state
    '''
    return df[df["State"] == state.upper()]

def city_donations(df: pd.DataFrame, city: str, state: str) -> pd.DataFrame:
    '''
    returns subset of the data with donations in the given city and state
    '''
    return df[(df["City"].str.lower() == str(city).lower()) & (df["State"] == state.upper())]

def unique_cities(df: pd.DataFrame) -> int:
    '''
    returns the number of unique cities in the dataframe
    '''
    return len(df["City"].str.lower().unique())

def stats_by_state(df: pd.DataFrame) -> pd.DataFrame:
    '''
    returns a dataframe where index is state abbreviations, columns are
        number of donors,
        number of unique cities donated from,
        total donation amount,
        donations in the past 18 months,
        most recent donation date
    '''
    # ensure required cols exist
    for col in ["State", "City", "Account ID", "Total Gifts (All Time)", "Number of Gifts Past 18 Months"]:
        if col not in df.columns:
            df[col] = np.nan
    # copy data and drop rows where there is no state
    df["State"] = df["State"].replace("", np.nan)
    data = df.copy().dropna(subset=["State"])

    # normalize New York naming
    data["State"] = data["State"].replace({"NY": "New York", "ny": "New York"})

    # group by city and create dataframe
    g = data.groupby("State")
    res = pd.DataFrame({
        "Cities" : g["City"].nunique(),
        "Donors" : g["Account ID"].nunique(),
        "Total Gifts (All Time)" : g["Total Gifts (All Time)"].sum(),
        "Number of Gifts Past 18 Months" : g["Number of Gifts Past 18 Months"].sum().astype(int)
    })

    # remove canada
    canadian_states = ["AB", "BC", "MB", "NB", "NL", "NT", "NS", "NU", "ON", "PE", "QC", "SK", "YT"]
    res.drop(canadian_states, inplace=True, errors="ignore")

    # sort and format
    res = res.sort_values(by=["Donors", "Total Gifts (All Time)"], ascending=[False, False])
    res["Total Gifts (All Time)"] = res["Total Gifts (All Time)"].apply(lambda x: "${:,.2f}".format(x))
    return res

def stats_by_city(df: pd.DataFrame) -> pd.DataFrame:
    '''
    returns a dataframe where index is city name, columns are
        state,
        number of donors,
        total donation amount,
        donations in the past 18 months,
        most recent donation date
    '''
    # ensure required cols exist
    for col in ["City", "State", "Account ID", "Total Gifts (All Time)", "Number of Gifts Past 18 Months"]:
        if col not in df.columns:
            df[col] = np.nan
    # copy data and drop rows where city or state are null
    df = df.replace("", np.nan)
    data =  df.copy().dropna(subset=["City", "State"])

    # group by city and state and create dataframe
    g = data.groupby(["City", "State"])
    res = pd.DataFrame({
        "Donors" : g["Account ID"].nunique(),
        "Total Gifts (All Time)" : g["Total Gifts (All Time)"].sum(),
        "Number of Gifts Past 18 Months" : g["Number of Gifts Past 18 Months"].sum().astype(int)
    })

    # sort and format
    res = res.sort_values(by=["Donors", "Total Gifts (All Time)"], ascending=False)
    res["Total Gifts (All Time)"] = res["Total Gifts (All Time)"].apply(lambda x: "${:,.2f}".format(x))
    return res

def stats_no_location(df: pd.DataFrame) -> pd.DataFrame:
    '''
    returns a dataframe with rows that have country only or no location info, columns are
        Donors
        Total Gifts (All Time)
        Number of Gifts Past 18 Months
    '''
    res = pd.DataFrame(index = ["Country Only", "No Location"])
    df = df.replace("", np.nan)

    # country only
    data = df[df["City"].isnull() & (df["State"].isnull()) & df["Country"].notnull()]
    res.loc["Country Only", "Donors"] = data["Account ID"].nunique()
    res.loc["Country Only", "Total Gifts (All Time)"] = total_donations(data)
    res.loc["Country Only", "Number of Gifts Past 18 Months"] = data["Number of Gifts Past 18 Months"].sum().astype(int)

    # no location
    data = df[df["City"].isnull() & (df["State"].isnull()) & df["Country"].isnull()]
    res.loc["No Location", "Donors"] = data["Account ID"].nunique()
    res.loc["No Location", "Total Gifts (All Time)"] = total_donations(data)
    res.loc["No Location", "Number of Gifts Past 18 Months"] = data["Number of Gifts Past 18 Months"].sum().astype(int)

    res["Total Gifts (All Time)"] = res["Total Gifts (All Time)"].apply(lambda x: "${:,.2f}".format(x))
    return res

# stats by time

def stats_by_year(df: pd.DataFrame) -> pd.DataFrame:
    '''
    returns a dataframe with year and number of donors who made their last donation in that year
    '''
    g = df.groupby(df["Last Gift Date"].dt.year.rename("Year"))
    res = pd.DataFrame({"Donors" : g["Account ID"].nunique()})
    return res

def stats_by_month(df: pd.DataFrame) -> pd.DataFrame:
    '''
    returns a dataframe with month and number of donors who made their last donation in that month
    '''
    # group by numeric month
    g = df.groupby(df["Last Gift Date"].dt.month)["Account ID"].nunique()
    # ensure months are ordered Jan..Dec and fill missing with 0
    month_order = list(range(1, 13))
    g = g.reindex(month_order, fill_value=0)
    res = pd.DataFrame({
        "Month": [calendar.month_abbr[m] for m in month_order],
        "MonthNum": month_order,
        "Donors": g.values,
    })
    return res
