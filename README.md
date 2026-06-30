# USGS Station Data Downloader

A Windows-friendly Streamlit application for discovering, reviewing, and downloading time-series data from selected USGS monitoring stations.

This tool allows users to enter USGS station IDs, inspect available data series, review station metadata, visualize station locations on a map, and download selected datasets for a user-defined time period. The downloaded results are automatically saved as organized Excel files.

---

## Project Overview

The **USGS Station Data Downloader** is designed to simplify the process of accessing hydrological and groundwater monitoring data from the United States Geological Survey (USGS) web services.

Instead of manually editing Python code or working inside a Jupyter Notebook, this application provides a clear graphical interface where users can:

- Enter one or more USGS station IDs
- Select the desired data category
- Inspect all available data series for each station
- Review station metadata
- View station locations on a map
- Choose a custom start and end date
- Download selected time-series data
- Export all results into structured Excel files

This application is useful for groundwater, surface-water, streamflow, water-quality, precipitation, atmospheric, environmental, and hydrological data analysis projects.

---

## Main Features

### Station Input

Users can enter one or multiple USGS station IDs.

Each station ID should be entered on a separate line.

Example:

```text
453027099505001
453358098260101
451605097071701
```

The app also includes a cleaning function that can extract the numeric USGS station ID from pasted text.

---

### Data Group Selection

Users can select one or more data groups from the sidebar.

Available options include:

```text
ALL
streamflow
surface_water_levels
groundwater_level
spring_water_level
water_quality
precipitation
atmospheric
other
```

If `ALL` is selected, the app displays all available data series for the selected stations.

---

### Station Discovery

Before downloading data, the app first queries the USGS Site Web Service to discover the exact available data series for the selected stations.

The discovery step provides:

- Station number
- Station name
- Site type
- Data type code
- Parameter code
- Statistic code
- Available period of record
- Number of observations
- Dashboard-style data group classification
- Download support status

This step helps users clearly understand what data is available before starting the download process.

---

### Station Metadata

The application retrieves expanded station information, including:

- Agency code
- Station number
- Station name
- Site type
- Latitude
- Longitude
- Coordinate datum
- Elevation
- Elevation datum
- Hydrologic unit code
- State code
- County code
- Time zone
- Well depth
- Hole depth
- Aquifer code
- Aquifer type code

This information is displayed inside the app and also saved as an Excel file.

---

### Station Map

If latitude and longitude values are available, the application displays the selected stations on a map.

This helps users visually check the spatial location of the selected monitoring sites.

---

### Time-Series Download

After reviewing the available data series, users can select a start date and an end date and then begin the download process.

The current version supports the following USGS data types:

```text
iv
uv
rt
dv
gw
```

These correspond to instantaneous values, daily values, real-time values, and groundwater-level records depending on the USGS service response.

---

### Excel Output

All outputs are automatically saved in a structured output folder.

The application creates summary Excel files and individual station-based time-series Excel files.

---

## Project Folder Structure

The recommended project structure is:

```text
USGS_App/
│
├── app.py
├── requirements.txt
├── run_app.bat
└── outputs/
```

### File Descriptions

| File or Folder | Description |
|---|---|
| `app.py` | Main Streamlit application file |
| `requirements.txt` | List of required Python packages |
| `run_app.bat` | Windows batch file for launching the app easily |
| `outputs/` | Folder where all Excel outputs are saved |

---

## Requirements

The application requires Python and the following Python packages:

```text
streamlit
pandas
requests
openpyxl
```

These packages are listed in the `requirements.txt` file.

---

## Installation on Windows

### Step 1: Download or Clone the Repository

Download the project folder or clone the repository:

```bash
git clone https://github.com/your-username/USGS-Station-Data-Downloader.git
```

Move into the project directory:

```bash
cd USGS-Station-Data-Downloader
```

---

### Step 2: Create a Virtual Environment

Create a Python virtual environment:

```bash
python -m venv .venv
```

---

### Step 3: Activate the Virtual Environment

Activate the virtual environment on Windows:

```bash
.venv\Scripts\activate
```

---

### Step 4: Install Required Packages

Install all required packages:

```bash
pip install -r requirements.txt
```

---

### Step 5: Run the Application

Run the Streamlit app:

```bash
streamlit run app.py
```

After running this command, the application will open in your web browser.

---

## Easy Windows Launch Method

For easier daily use, a Windows batch file named `run_app.bat` can be used.

The content of `run_app.bat` should be:

```bat
@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
streamlit run app.py
pause
```

After the virtual environment and required packages are installed, users can simply double-click:

```text
run_app.bat
```

This will automatically activate the environment and launch the application.

---

## How to Use the Application

### Step 1: Open the App

Run the app using:

```bash
streamlit run app.py
```

or double-click:

```text
run_app.bat
```

---

### Step 2: Enter USGS Station IDs

In the sidebar, enter one or more USGS station IDs.

Each station ID should be placed on a separate line.

Example:

```text
453027099505001
453358098260101
451605097071701
```

---

### Step 3: Select Data Groups

Choose the desired data group from the sidebar.

For groundwater-level data, select:

```text
groundwater_level
```

To inspect all available station data, select:

```text
ALL
```

---

### Step 4: Select Output Folder

The default output folder is:

```text
outputs
```

Users can change this path if needed.

---

### Step 5: Select Start and End Date

Choose the date range for downloading data.

Example:

```text
Start date: 2000-01-01
End date: 2026-06-30
```

The start date must be earlier than or equal to the end date.

---

### Step 6: Discover Available Station Data

Click:

```text
1) Discover available station data
```

The app will retrieve and display:

- Available time-series records
- Station metadata
- Station locations
- Download-supported series
- Period of record
- Observation count

This step should always be completed before downloading data.

---

### Step 7: Review the Available Data

After discovery, review the displayed tables carefully.

The main available-series table includes important columns such as:

| Column | Meaning |
|---|---|
| `site_no` | USGS station number |
| `station_nm` | Station name |
| `site_tp_cd` | USGS site type code |
| `dashboard_groups` | Classified data group |
| `data_type_cd` | USGS data type code |
| `parm_cd` | USGS parameter code |
| `stat_cd` | USGS statistic code |
| `begin_date` | First available date |
| `end_date` | Last available date |
| `count_nu` | Number of available records |
| `download_supported` | Whether the current app can download this series |

---

### Step 8: Download Selected Data

After reviewing the selected series, click:

```text
2) Download selected data
```

The application will download the available supported time-series data for the selected date range.

A progress bar will show the download status.

---

## Output Files

The app creates the following files inside the output directory:

```text
outputs/
│
├── 01_exact_available_series_period_of_record.xlsx
├── 02_selected_series.xlsx
├── 03_location_details_and_information.xlsx
├── 04_download_log.xlsx
└── time_series_excels/
```

### Output File Descriptions

| Output File | Description |
|---|---|
| `01_exact_available_series_period_of_record.xlsx` | Complete inventory of all available data series for the selected stations |
| `02_selected_series.xlsx` | Filtered data series based on the selected data groups |
| `03_location_details_and_information.xlsx` | Expanded station metadata and location information |
| `04_download_log.xlsx` | Download status, number of rows, output file paths, and request URLs |
| `time_series_excels/` | Folder containing station-based time-series Excel files |

---

## Time-Series Excel Files

For each station, the app creates a separate Excel file inside:

```text
outputs/time_series_excels/
```

Example filename:

```text
USGS_453027099505001_2000-01-01_to_2026-06-30.xlsx
```

Each station Excel file may contain multiple sheets, including:

| Sheet Type | Description |
|---|---|
| `selected_series` | The selected data series for the station |
| Full time-series sheets | Complete downloaded data with metadata |
| `min_...` sheets | Simplified time-series sheets with essential columns |

---

## Important Output Columns

The downloaded time-series data may include the following columns:

| Column | Description |
|---|---|
| `site_no` | USGS station number |
| `station_nm` | Station name |
| `datetime_raw` | Original datetime from USGS |
| `datetime_utc` | Parsed datetime in UTC |
| `datetime` | Clean datetime column for Excel |
| `value` | Downloaded observation value |
| `unit` | Measurement unit |
| `variable_code` | USGS variable code |
| `variable_name` | USGS variable name |
| `variable_description` | Description of the variable |
| `qualifiers` | USGS data qualifiers |
| `requested_data_type_cd` | Requested data type |
| `requested_parm_cd` | Requested parameter code |
| `requested_stat_cd` | Requested statistic code |
| `period_begin_date` | Start of available period of record |
| `period_end_date` | End of available period of record |
| `period_count_nu` | Number of records in the USGS inventory |

---

## Supported Data Types

The current version of the application supports downloading the following USGS data types:

```text
iv
uv
rt
dv
gw
```

Some data series may appear in the USGS inventory but may not be downloaded by this version of the app. These rows are still displayed so users can understand the full available data inventory.

---

## Data Group Classification Logic

The app classifies available USGS records into dashboard-style groups using parameter codes, site type codes, data type codes, and parameter descriptions.

Examples:

| Data Group | Typical Indicators |
|---|---|
| `streamflow` | Parameter code `00060`, discharge, streamflow |
| `surface_water_levels` | Parameter code `00065`, gage height, stage |
| `groundwater_level` | Groundwater site type, groundwater data type, groundwater-level parameter codes |
| `spring_water_level` | Spring site type or spring-related station name |
| `water_quality` | Water temperature, pH, dissolved oxygen, nitrate, turbidity, conductance |
| `precipitation` | Parameter code `00045`, rainfall, precipitation |
| `atmospheric` | Air temperature, wind, humidity, barometric pressure |
| `other` | Data that does not match the above groups |

---

## Example Workflow

A typical workflow is:

```text
1. Open the application.
2. Enter USGS station IDs.
3. Select groundwater_level or another data group.
4. Click "Discover available station data".
5. Review available series, metadata, and map.
6. Select the desired date range.
7. Click "Download selected data".
8. Open the generated Excel files in the outputs folder.
```

---

## Example Station Input

```text
453027099505001
453358098260101
451605097071701
```

---

## Troubleshooting

### The app does not open

Make sure the virtual environment is activated and dependencies are installed:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---

### `streamlit` is not recognized

This usually means Streamlit is not installed in the active environment.

Run:

```bash
pip install streamlit
```

or reinstall all dependencies:

```bash
pip install -r requirements.txt
```

---

### No data is downloaded

Possible reasons:

- The selected station has no data for the chosen date range.
- The selected data series is not supported by the current version of the app.
- The USGS service returned an empty response.
- The station ID is incorrect.
- The requested parameter is available in the inventory but not downloadable from the selected endpoint.

Check:

```text
04_download_log.xlsx
```

This file contains the download status and request URL for each attempted download.

---

### Some rows are marked as not supported

The app displays all available USGS inventory rows, but only the following data types are downloaded by this version:

```text
iv
uv
rt
dv
gw
```

Rows with other data types are kept in the inventory table for transparency but are not downloaded.

---

### Excel file has many sheets

This is expected.

Each station file can contain:

- One sheet for selected series
- One or more sheets for full downloaded data
- One or more simplified sheets for quick analysis

This structure helps separate different parameters, statistics, and data types.

---

## Notes

- The app uses USGS web services.
- Internet connection is required.
- Very long date ranges or many stations may take longer to download.
- USGS responses may differ depending on station availability and data type.
- The app saves timezone-cleaned datetime values to avoid Excel export issues.
- The app is designed primarily for Windows users, but it can also run on macOS and Linux if Python and the required packages are installed.

---

## Recommended Use Cases

This application can be used for:

- Groundwater-level data collection
- Hydrological time-series analysis
- USGS station screening
- Water resources research
- Environmental engineering projects
- Civil engineering and hydrology coursework
- Data preparation for machine learning models
- Long-term monitoring data extraction

---

## License

This project is intended for educational and research use.

You may modify and extend the code according to your project requirements.

---

## Acknowledgment

This application retrieves data from the United States Geological Survey web services.

USGS data availability, metadata, parameter codes, and station records are controlled by USGS services.


## Contact me

Amir Haddadd (amir6haddadi@gmail.com)
