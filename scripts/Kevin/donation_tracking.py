import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
 
repo_root = Path(__file__).resolve().parents[2] #creates a root relative to this file 
csv_path = repo_root / 'data' / 'Riverkeeper_Donors_for_NYU_Biokind_Project-10.22.25.csv' #accesses cleaned.csv using Path "/"

data = pd.read_csv(csv_path, parse_dates=['Last Gift Date'])

data['Year'] = data['Last Gift Date'].dt.year #extracts the year 
data['Month'] = data['Last Gift Date'].dt.month #extracts the month 

monthly_donations = ( 
    data.groupby(['Year', 'Month'])['Total Gifts (All Time)']
    .sum() #sums up the total by year + month 
    .reset_index() #assigns a new index and turns the old one into a column
)
def pie_maker(size1, size2, values, labels, autopct, startangle, colors, shadow, title):
    '''Creates a pie chart with the given parameters.''' 
    plt.figure(figsize=(size1,size2))
    plt.pie(
        values,
        labels=labels,
        autopct=autopct,
        startangle=startangle,
        colors=colors,
        shadow=shadow
    )
    plt.title(title)
    plt.show()

df = pd.DataFrame(monthly_donations) #turned monthly donations into dataframe
pf = pd.DataFrame(data) #turned the parsed data into a dataframe

max_value = monthly_donations['Total Gifts (All Time)'].max() #found the max amount donated

#bar chart
for year, group in monthly_donations.groupby('Year'): #opens a new chart window for each year 
    plt.bar(group['Month'], group['Total Gifts (All Time)'])
    plt.title(f'Amount of Money Donated by Month in {year}')
    plt.xlabel('Month')
    plt.ylabel('Money ($)')
    plt.ylim(0, max_value) 
    plt.show()

#pie chart 
colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']

bins = [1, 250, 5000, 100000, float('inf')]
labels = ["Small ($1-250)", "Medium ($250-5k)", "Large ($5k-$100k)", "Major ($100k+)" ]
pf['donation_range'] = pd.cut(pf['Total Gifts (All Time)'], bins = bins, labels = labels, right = False)

donation_summary = (
    pf.groupby('donation_range')['Total Gifts (All Time)']
    .sum()
    .reindex(labels)
)#sums up the money by donation range 


#counts the number of donors per donation range  
count_summary = (
    pf['donation_range']
    .value_counts()
    .reindex(labels)
)

#shows the distribution of donations by range
pie_maker(10,10, donation_summary, donation_summary.index, '%1.1f%%', 90, colors, True, 'Distribution of Donations by Range')

pie_maker(10,10, count_summary, count_summary.index, '%1.1f%%', 90, colors, True, 'Distribution of Donors by Range')


print(monthly_donations) # checking values are being represented correctly


#generate pychart as image 