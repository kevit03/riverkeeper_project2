import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd

 
repo_root = Path(__file__).resolve().parents[2] #creates a root relative to this file 
csv_path = repo_root / 'scripts' / 'Izzy' / 'cleaned.csv' #accesses cleaned.csv using Path "/"

data = pd.read_csv(csv_path, parse_dates=['last_gift_date'])

data['Year'] = data['last_gift_date'].dt.year #extracts the year 
data['Month'] = data['last_gift_date'].dt.month #extracts the month 

monthly_donations = ( 
    data.groupby(['Year', 'Month'])['total_gifts_amount']
    .sum() #sums up the total by year + month 
    .reset_index() #assigns a new index and turns the old one into a column
)


df = pd.DataFrame(monthly_donations)
pf = pd.DataFrame(data)

max_value = monthly_donations['total_gifts_amount'].max()

#bar chart
for year, group in monthly_donations.groupby('Year'): #opens a new chart window for each year 
    plt.bar(group['Month'], group['total_gifts_amount'])
    plt.title(f'Amount of Money Donated by Month in {year}')
    plt.xlabel('Month')
    plt.ylabel('Money ($)')
    plt.ylim(0, max_value) 
    plt.show()

#pie chart 
colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']

bins = [1, 250, 5000, 100000, float('inf')]
labels = ["Small ($1-250)", "Medium ($250-5k)", "Large ($5k-$100k)", "Major ($100k+)" ]
pf['donation_range'] = pd.cut(pf['total_gifts_amount'], bins = bins, labels = labels, right = False)

donation_summary = (
    pf.groupby('donation_range')['total_gifts_amount']
    .sum()
    .reindex(labels)
)#sums up the money by donation range 

plt.pie(
    donation_summary,
    labels=donation_summary.index,
    autopct='%1.1f%%',
    startangle=90,
    colors=colors, #i like colors, need to figure how to change font 
    shadow=True 
    
)

plt.title('Distribution of Donations by Range')
plt.show()

count_summary = (
    pf['donation_range']
    .value_counts()
    .reindex(labels)
)
#counts the number of donors per donation range 

plt.pie(
    count_summary,
    labels=count_summary.index,
    autopct='%1.1f%%',
    startangle=90,
    colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'],
    shadow=True
)

plt.title('Percentage of Donors per Donation Range')
plt.show()


print(monthly_donations) # checking values are being represented correctly

