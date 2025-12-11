# Riverkeepers Project 2
This project is a data driven initiative built by the Biokind Team at NYU to analyze and strengthen community around the Hudson River water conservation at Riverkeepers. We take donor data and transform the raw data into actionable data insight. 

![Biokind Analytics](https://github.com/Pk0704/riverkeeper_project2/blob/main/scripts/Kevin/biokind.png)

## Built With 
[Streamlit](https://streamlit.io/) - open source framework that our application is deployed onto 

[Geopy](https://geopy.readthedocs.io/en/stable/) - used to geocode and cache results

## Key Features 
-> **Global Interactive Heatmap**

-> **Automated Geocaching**

-> **Partitioned Charts and Visualizations**

-> **Data Cleaning of Over 8,000 entries**

## Getting Started

There are **two ways** to run the dashboard:

1. **One-click launchers (recommended for non-technical users)**
2. **Manual setup via terminal (for developers)**

You will still need **Python 3.10+** installed on your machine.

---

### Option 1 – One-Click Launchers (Recommended)

After downloading or cloning this repository, you can start the dashboard by double-clicking a launcher file. On first run, the project will:

- Create a local virtual environment (`.venv`) if it does not exist  
- Install all Python dependencies from `requirements.txt` **once**  
- Start the Streamlit app

On subsequent runs, it will reuse the existing `.venv` and **skip** dependency installation.

#### macOS

1. Make sure you have **Python 3.10+** installed (e.g. via Homebrew or the official installer).
2. Download / clone the repo and open the project folder in Finder.
3. In the project root, locate:

   `Run Riverkeeper.command`

4. **First run only:** macOS may block the file as coming from an unidentified developer.  
   - Right-click (or Ctrl-click) `Run Riverkeeper.command`  
   - Select **“Open”**  
   - Confirm that you want to open it
5. A Terminal window will open and you will see logs such as:
   - Creating `.venv` (first run only)
   - Installing dependencies (first run only)
   - Running Streamlit via `launch.py`
6. When the app starts, your browser should open automatically at the Riverkeeper dashboard.

To stop the app, close the browser tab and press `Ctrl+C` in the Terminal window, then close the window.

#### Windows

1. Make sure you have **Python 3.10+** installed and the `py` launcher available.
2. Download / clone the repo and open the project folder in File Explorer.
3. In the project root, locate:

   `run_dashboard.bat`

4. Double-click `run_dashboard.bat` to start the dashboard.
   - On first run, Windows SmartScreen may show a warning.  
   - Click **“More info”** → **“Run anyway”** if prompted.
5. A Command Prompt window will open and you will see logs such as:
   - Creating `.venv` (first run only)
   - Installing dependencies (first run only)
   - Running Streamlit via `launch.py`
6. When the app starts, your default browser should open automatically at the Riverkeeper dashboard.

To stop the app, close the browser tab and press `Ctrl+C` in the Command Prompt window, then close the window.

> Note: The `.venv` folder is created locally and should **not** be committed to version control.

---

### Option 2 – Manual Setup (For Developers)

If you prefer to manage the environment yourself (or run without the launchers):

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
streamlit run app/front.py
```

---

# Donor Data Upload – CSV Format

To use the Riverkeeper donor dashboard, please upload a CSV file with a specific set of columns and formats.

The app expects exactly the following structure / base columns (names must match, including spaces and capitalization):

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

NOTE: The current pipelines do not use `BFPO No` or `Postcode`, because they were not present in the data we worked with.

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

When the report is created, **do not rename the columns** in Excel/Numbers/Google Sheets and after, save and upload the CSV file into the Riverkeeper donor dashboard when prompted.

Once the CSV follows this format, the dashboard should be able to read it and generate the maps, charts, and summaries automatically.

## Caching and geocoding

- Geocode cache: `app/data/geocode_cache.json` (auto-created if missing).
- Location cache: `app/data/RiverKeeper_Donors_Unique_Locations.csv` (auto-created if missing).
- Donors without City/State/Country are excluded from the map but still appear in aggregate statistics.
