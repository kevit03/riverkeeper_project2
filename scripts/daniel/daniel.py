import pandas as pd



df = pd.read_csv('/Users/danielliang/Downloads/donor_data.csv')





df["Total Gifts (All Time)"] = (
    df["Total Gifts (All Time)"]
    .str.replace("[$,]", "", regex=True)
    .astype(float)
)
df["Last Gift Date"] = pd.to_datetime(df["Last Gift Date"])
df = df.dropna(subset=["Number of Gifts Past 18 Months"])


df["Segment"] = df["Number of Gifts Past 18 Months"].apply(
    lambda x: "Active" if x > 0 else "Inactive"
)


kpis = df.groupby("Segment").agg(
    Donor_Count=("Account ID", "count"),
    Total_Raised=("Total Gifts (All Time)", "sum"),
    Avg_Gift=("Total Gifts (All Time)", "mean"),
    Median_Gift=("Total Gifts (All Time)", "median"),
    Avg_Gifts_Past_18M=("Number of Gifts Past 18 Months", "mean"),
    Latest_Gift=("Last Gift Date", "max"),
    Earliest_Gift=("Last Gift Date", "min"),
).round(2)

print("=== KPI Summary by Segment ===")
print(kpis.T)


print("\n=== Overall KPIs ===")
print(f"Total Donors:       {len(df)}")
print(f"Active Donors:      {(df['Segment'] == 'Active').sum()}")
print(f"Inactive Donors:    {(df['Segment'] == 'Inactive').sum()}")
print(f"Active Rate:        {(df['Segment'] == 'Active').mean():.1%}")
print(f"Total Raised:       ${df['Total Gifts (All Time)'].sum():,.0f}")


print("\n=== Top 10 States by Active Donors ===")
state_seg = df[df["Segment"] == "Active"].groupby("State")["Account ID"].count()
print(state_seg.sort_values(ascending=False).head(10))


print("\n=== Gift Frequency Distribution (Active Donors) ===")
print(df[df["Segment"] == "Active"]["Number of Gifts Past 18 Months"].value_counts().sort_index())
