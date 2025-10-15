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

max_value = monthly_donations['total_gifts_amount'].max()

for year, group in monthly_donations.groupby('Year'): #opens a new chart window for each year 
    plt.bar(group['Month'], group['total_gifts_amount'])
    plt.title(f'Amount of Money Donated by Month in {year}')
    plt.xlabel('Month')
    plt.ylabel('Money ($)')
    plt.ylim(0, max_value) 
    plt.show()

print(monthly_donations) #double checking values are being represented correctly 

