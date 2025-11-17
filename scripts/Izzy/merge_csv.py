import pandas as pd

def shared_and_unique_rows(df1: pd.DataFrame, df2: pd.DataFrame, col: str) -> tuple:
    '''
    takes two dataframes with a common column and returns a tuple of 
        number of shared rows, 
        number of rows unique to dataframe 1,
        number of rows unique to dataframe 2
    '''
    shared = list(set(df1[col]).intersection(set(df2[col])))
    df1_unique = df1[~df1[col].isin(shared)]
    df2_unique = df2[~df2[col].isin(shared)]
    return (len(shared), df1_unique.shape[0], df2_unique.shape[0])

def merge_csv(fp_old: str, fp_new: str) -> pd.DataFrame:
    '''
    takes old csv filepath and updated csv filepath, merges into one dataframe, saves as a csv, and returns the merged dataframe \n
    columns of csvs should be 
        Account ID,
        City,
        State,
        BFPO No,
        Postcode,
        Country,
        Total Gifts (All Time),
        Last Gift Date
        Number of Gifts Past 18 Months
    and any column except Account ID can appear in only one csv
    '''
    # read old and new csv to dataframe
    df_old = pd.read_csv(fp_old)
    df_new = pd.read_csv(fp_new)

    # make sure dataframe columns match
    df_old.rename(columns={"Total Gifts Amount": "Total Gifts (All Time)"}, inplace=True)
    print(df_old.columns)
    print(df_new.columns)

    # display number of shared rows and rows unique to each dataset
    rows = shared_and_unique_rows(df_old, df_new, "Account ID")
    print(f"Merging {rows[0]} shared rows, {rows[1]} rows unique to old dataset, and {rows[2]} rows unique to new dataset.")

    # outer merge on account id
    df_merged = df_old.merge(df_new, on="Account ID", how="outer")

    # remove duplicate columns by taking the value from the new dataframe
    # if the value is null in the new dataframe, take the value from the old dataframe
    for col in df_merged.columns:
        if col.endswith("_x"):
            base = col[:-2]
            y_col = base + "_y"
            if y_col in df_merged.columns:
                df_merged[base] = df_merged[y_col].combine_first(df_merged[col])
                df_merged = df_merged.drop(columns=[col, y_col])

    # reorder columns
    col_order = ["Account ID", "City", "State", 
                 "BFPO No", "Postcode", "Country", 
                 "Total Gifts (All Time)", "Last Gift Date", 
                 "Number of Gifts Past 18 Months"]
    df_merged = df_merged[col_order]

    # make sure string columns are in uniform casing
    df_merged["City"] = df_merged["City"].str.title()
    df_merged["State"] = df_merged["State"].str.upper()
    df_merged["Country"] = df_merged["Country"].str.title()

    # convert merged dataframe to csv
    df_merged.to_csv("merged_data.csv", index=False)

    return df_merged

fp1 = "data/Riverkeeper_Donors.csv"
fp2 = "data/Riverkeeper_Donors_for_NYU_Biokind_Project-10.22.25.csv"
merge_csv(fp1, fp2)