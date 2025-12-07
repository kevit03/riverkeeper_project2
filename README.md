# Riverkeepers Project 2
This project is a data driven initiatve built by the Biokind Team at NYU to analyze and strengthen community around the Hudson River water conservation at Riverkeepers. We take donor data and transform the raw data into actionable data insight. 


![Biokind Analytics](https://github.com/Pk0704/riverkeeper_project2/blob/main/scripts/Kevin/biokind.png)

## Built With 
[Streamlit](https://streamlit.io/) - open source framework that our application is deployed onto 

[Geopy](https://geopy.readthedocs.io/en/stable/) - used to geocode and geocache 

## Key Features 
-> **Global Interactive Heatmap**

-> **Automated Geocaching**

-> **Partitioned Diagrams from Given Data**

-> **Data Cleaning of Over 8,000 entries**

## Getting Started - Running Instructions 
# Getting Started

Before uploading any data, please make sure you have the Python dependencies installed.

1. Make sure you have **Python 3.10+** installed.
2. In a terminal, inside the project folder, run:
```bash
python -m venv .venv
source .venv/bin/activate   # Mac / Linux
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

Once dependencies are installed, you can run the app:
```bash
streamlit run app.py
```

(If your entry file has a different name, replace `app.py` accordingly.)

---

# Donor Data Upload – CSV Format

To use the Riverkeeper donor dashboard, please upload a CSV file with a specific set of columns and formats.

The app expects exactly the following base columns (names must match, including spaces and capitalization):

- `Account ID`
- `City`
- `State`
- `BFPO No`
- `Postcode`
- `Country`
- `Total Gifts (All Time)`
- `Last Gift Date`
- `Number of Gifts Past 18 Months`

These correspond to the internal `BASE_COLUMNS` list used by the app:
```python
BASE_COLUMNS = [
    "Account ID",
    "City",
    "State",
    "BFPO No",
    "Postcode",
    "Country",
    "Total Gifts (All Time)",
    "Last Gift Date",
    "Number of Gifts Past 18 Months",
]
```

---

## 1. General File Requirements

- **File type:** CSV (`.csv`)
- **Encoding:** UTF-8
- **Separator:** Comma (`,`)
- **Header row:** The first row must be the column names listed above.
- **One row per record:** Each row represents one donor account.

> IMPORTANT: If any of the required columns are missing or renamed, the app may not load the file correctly.

---

## 2. Column Definitions and Expected Formats

| Column name | Required? | Example value | Description |
|-------------|-----------|---------------|-------------|
| `Account ID` | ✅ Yes | `001PY00000cQeQaYAK` | Unique identifier for the donor account (e.g. Salesforce Account ID). Used to keep rows distinct. |
| `City` | ✅ Yes* | `Newburgh` | City where the donor is located. Used for mapping and regional summaries. |
| `State` | ✅ Yes* | `NY` | Two-letter state or region code (e.g. `NY`, `NJ`, `CA`). Used with City and Country for geocoding. |
| `BFPO No` | Optional | `BF2` | British Forces Post Office number (typically empty for U.S.-based donors). |
| `Postcode` | Optional | `12561` or `BF2 0LP` | Postal / ZIP code. Used to improve geocoding when available. |
| `Country` | ✅ Yes | `United States` | Country name (e.g. `United States`). Used for mapping and filtering. |
| `Total Gifts (All Time)` | ✅ Yes | `$9,750.00` | Lifetime total gifts per account, formatted as a currency string. The app converts this to a numeric value. |
| `Last Gift Date` | ✅ Yes | `11/27/2024` | Date of the most recent gift in `MM/DD/YYYY` format (e.g. `3/1/2023`, `11/27/2024`). |
| `Number of Gifts Past 18 Months` | ✅ Yes | `0`, `1`, `147` | Number of gifts in the last 18 months (non-negative integer). Used to track recent engagement. |

*For geographic maps, at least either:

- a valid `Postcode`, **or**
- a combination of `City`, `State`, and `Country`

should be present. Donors without any usable location information may not appear on the map, but will still be counted in aggregate metrics.

NOTE: Our model does not use `BFPO No` or `Postcode`, due to them not being present in the data we worked with.

---

## 3. Data Format Details

### Currency formatting

- **Column:** `Total Gifts (All Time)`
- **Expected format:**
  - Dollar sign and two decimal places, e.g.
    - `$1,500.00`
    - `$79,400.00`
  - Commas for thousands are fine.
- The app automatically strips `$`, commas, and spaces before converting to numeric values.

### Date formatting

- **Column:** `Last Gift Date`
- **Expected format:**
  - U.S. style month/day/year (`MM/DD/YYYY`), e.g.
    - `3/11/2024`
    - `11/27/2024`
  - Time of day is not required and will be ignored if present.

### Numeric formatting

- **Column:** `Number of Gifts Past 18 Months`
- **Expected values:**
  - Non-negative whole numbers: `0`, `1`, `2`, …
  - Blank values will typically be treated as `0` or may be excluded from certain calculations, depending on the analysis.

### Missing values

- `BFPO No` and `Postcode` can be blank for many donors (especially U.S.-based).
- **Please try to keep `City`, `State`, and `Country` filled whenever possible so donors show up on location-based views**.
- Rows missing `Total Gifts (All Time)` or `Last Gift Date` may not be usable in some revenue or recency charts.

---

## 4. Uploading file

When the report is created, **Do not rename the columns** in Excel/Numbers/Google Sheets and after, save and upload the CSV file into the Riverkeeper donor dashboard when prompted.

Once the CSV follows this format, the dashboard should be able to read it and generate the maps, charts, and summaries automatically.

