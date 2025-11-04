import numpy as np
import pandas as pd
from core_analysis import *

df = pd.read_csv("data/merged_dataset.csv")
df["last_gift_date"] = pd.to_datetime(df["last_gift_date"])

print(stats_by_state(df))