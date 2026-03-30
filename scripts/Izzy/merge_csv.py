import pandas as pd

def merge_csv(df_old: pd.DataFrame, df_new: pd.DataFrame, save=True) -> tuple[pd.DataFrame, pd.DataFrame]:
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

    # if the old df is empty, just return the new one
    if df_old.empty:
        return df_new, df_new

    # make sure dataframe columns match
    df_old.rename(columns={"Total Gifts Amount": "Total Gifts (All Time)"}, inplace=True)

    # display number of shared rows and rows unique to each dataset
    shared = list(set(df_old["Account ID"]).intersection(set(df_new["Account ID"])))
    df1_unique = df_old[~df_old["Account ID"].isin(shared)]
    df2_unique = df_new[~df_new["Account ID"].isin(shared)]
    rows = (len(shared), df1_unique.shape[0], df2_unique.shape[0])
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

    if save:
        # convert merged dataframe to csv
        df_merged.to_csv("merged_data.csv", index=False)

        # convert new rows to csv
        df2_unique.to_csv("new_data.csv", index=False)

    return df_merged, df2_unique