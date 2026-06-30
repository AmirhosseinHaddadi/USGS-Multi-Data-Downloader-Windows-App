import re
import time
from io import StringIO
from pathlib import Path
from datetime import date

import requests
import pandas as pd
import streamlit as st


BASE_URL = "https://waterservices.usgs.gov/nwis"

ENDPOINTS = {
    "site": f"{BASE_URL}/site/",
    "iv": f"{BASE_URL}/iv/",
    "dv": f"{BASE_URL}/dv/",
    "gwlevels": f"{BASE_URL}/gwlevels/",
}

HEADERS = {
    "User-Agent": "Python USGS Monitoring Locations Downloader",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
}

SUPPORTED_DOWNLOAD_DATA_TYPES = {"iv", "uv", "rt", "dv", "gw"}

DASHBOARD_GROUP_OPTIONS = [
    "ALL", "streamflow", "surface_water_levels", "groundwater_level",
    "spring_water_level", "water_quality", "precipitation", "atmospheric", "other",
]

GW_LEVEL_PARAMETER_CODES = {
    "00000", "62610", "62611", "72019", "72020",
    "72150", "72226", "72227", "72228", "72229",
    "72230", "72231",
}

ATMOSPHERIC_PARAMETER_CODES = {
    "00020", "00021", "00025", "00035", "00036",
    "00052", "00054", "00096",
}

PRECIPITATION_PARAMETER_CODES = {"00045"}

WATER_QUALITY_COMMON_PARAMETER_CODES = {
    "00010", "00095", "00300", "00400", "63680",
    "00631", "99133", "00665", "00940", "00915",
    "00925", "00930", "00935", "00945", "00955",
}


def clean_site_id(site_text):
    site_text = str(site_text).strip()
    matches = re.findall(r"\d{7,20}", site_text)
    if matches:
        return matches[-1]
    return site_text.replace("USGS", "").replace("-", "").strip()


def safe_name(text, max_len=31):
    text = str(text)
    text = re.sub(r"[^\w\-.]+", "_", text)
    text = text.strip("_")
    if not text:
        text = "sheet"
    return text[:max_len]


def normalize_blank(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def request_get(url, params=None, retries=3, sleep_seconds=1.2, allow_404=False):
    last_error = None
    for _attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=90)
            if response.status_code == 200:
                return response
            if allow_404 and response.status_code == 404:
                return response
            last_error = RuntimeError(
                f"HTTP {response.status_code}\n"
                f"URL: {response.url}\n"
                f"Message: {response.text[:700]}"
            )
        except Exception as exc:
            last_error = exc
        time.sleep(sleep_seconds)
    raise last_error


def parse_rdb(text):
    lines = []
    for line in text.splitlines():
        if line.strip() and not line.startswith("#"):
            lines.append(line)
    if len(lines) < 2:
        return pd.DataFrame()

    clean_text = "\n".join(lines)
    df = pd.read_csv(StringIO(clean_text), sep="\t", dtype=str)

    if len(df) > 0:
        first_row = df.iloc[0].astype(str).tolist()
        type_like_count = sum(bool(re.match(r"^\d+[snfd]$", item.strip())) for item in first_row)
        if type_like_count >= max(1, int(len(first_row) * 0.5)):
            df = df.iloc[1:].reset_index(drop=True)

    return df


def make_excel_safe(df):
    from datetime import datetime, timezone
    df = df.copy()

    def strip_timezone_value(x):
        if isinstance(x, pd.Timestamp):
            if x.tzinfo is not None:
                return x.tz_convert("UTC").tz_localize(None)
            return x
        if isinstance(x, datetime):
            if x.tzinfo is not None:
                return x.astimezone(timezone.utc).replace(tzinfo=None)
            return x
        return x

    for col in df.columns:
        if isinstance(df[col].dtype, pd.DatetimeTZDtype):
            df[col] = df[col].dt.tz_convert("UTC").dt.tz_localize(None)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            pass
        elif df[col].dtype == "object":
            df[col] = df[col].apply(strip_timezone_value)

    return df


def make_unique_sheet_name(base_name, used_sheet_names):
    base_name = safe_name(base_name, max_len=31)
    if base_name not in used_sheet_names:
        used_sheet_names.add(base_name)
        return base_name

    counter = 1
    while True:
        suffix = f"_{counter}"
        candidate = base_name[:31 - len(suffix)] + suffix
        if candidate not in used_sheet_names:
            used_sheet_names.add(candidate)
            return candidate
        counter += 1


def render_contact_section():
    st.divider()
    st.subheader("Contact / Support")
    st.caption(
        "If you encounter any issue, have a new idea, or want to suggest an improvement, "
        "feel free to contact me through the platforms below."
    )

    st.link_button("📧 Email · amir6haddadi@gmail.com", "mailto:amir6haddadi@gmail.com", use_container_width=True)
    st.link_button("🔗 LinkedIn · amirhossein-haddadi", "https://www.linkedin.com/in/amirhossein-haddadi-aa8b54282/", use_container_width=True)
    st.link_button("🎓 Google Scholar · Amirhossein Haddadi", "https://scholar.google.com/citations?view_op=list_works&hl=en&user=wqig0OcAAAAJ&gmla=AH8HC4xCJH62QdpTsbD8ZYfkkUQJSdYw63ZRcPHEDAqvEGrBzOE_Sjq94FLGWwNhDZSsV7pERKi3D6Do9FHZJZRi3k_Ffd3GmVin1hbxHLStq9zidg", use_container_width=True)
    st.link_button("💻 GitHub · AmirhosseinHaddadi", "https://github.com/AmirhosseinHaddadi", use_container_width=True)


def classify_dashboard_groups(row):
    parm_cd = normalize_blank(row.get("parm_cd", ""))
    data_type_cd = normalize_blank(row.get("data_type_cd", "")).lower()
    site_tp_cd = normalize_blank(row.get("site_tp_cd", "")).upper()
    station_nm = normalize_blank(row.get("station_nm", "")).lower()
    parameter_nm = normalize_blank(row.get("parameter_nm", "")).lower()
    parm_grp_cd = normalize_blank(row.get("parm_grp_cd", "")).lower()

    text = " ".join([station_nm, parameter_nm, parm_grp_cd]).lower()
    groups = set()

    if parm_cd == "00060" or "discharge" in text or "streamflow" in text:
        groups.add("streamflow")

    if parm_cd == "00065" or "gage height" in text or "stage" in text:
        groups.add("surface_water_levels")

    if (
        data_type_cd == "gw"
        or site_tp_cd.startswith("GW")
        or parm_cd in GW_LEVEL_PARAMETER_CODES
        or "groundwater" in text
        or "depth to water" in text
    ):
        groups.add("groundwater_level")

    if site_tp_cd.startswith("SP") or "spring" in station_nm:
        groups.add("spring_water_level")

    if (
        data_type_cd == "qw"
        or parm_cd in WATER_QUALITY_COMMON_PARAMETER_CODES
        or "water temperature" in text
        or "specific conductance" in text
        or "ph" in text
        or "dissolved oxygen" in text
        or "turbidity" in text
        or "nitrate" in text
        or "phosphorus" in text
    ):
        groups.add("water_quality")

    if parm_cd in PRECIPITATION_PARAMETER_CODES or "precipitation" in text or "rain" in text:
        groups.add("precipitation")

    if (
        parm_cd in ATMOSPHERIC_PARAMETER_CODES
        or "air temperature" in text
        or "barometric" in text
        or "wind" in text
        or "humidity" in text
        or "atmospheric" in text
    ):
        groups.add("atmospheric")

    if not groups:
        groups.add("other")

    return ",".join(sorted(groups))


def discover_available_series(station_ids):
    params = {
        "format": "rdb",
        "sites": ",".join(station_ids),
        "outputDataTypeCd": "all",
        "siteStatus": "all",
    }
    response = request_get(ENDPOINTS["site"], params=params)
    inventory_df = parse_rdb(response.text)

    if inventory_df.empty:
        return inventory_df

    inventory_df["dashboard_groups"] = inventory_df.apply(classify_dashboard_groups, axis=1)

    if "count_nu" in inventory_df.columns:
        inventory_df["count_nu_numeric"] = pd.to_numeric(inventory_df["count_nu"], errors="coerce")

    if "begin_date" in inventory_df.columns:
        inventory_df["begin_date_parsed"] = pd.to_datetime(inventory_df["begin_date"], errors="coerce")

    if "end_date" in inventory_df.columns:
        inventory_df["end_date_parsed"] = pd.to_datetime(inventory_df["end_date"], errors="coerce")

    return inventory_df


def select_requested_series(inventory_df, requested_groups):
    if inventory_df.empty:
        return inventory_df

    selected_df = inventory_df.copy()

    if "ALL" not in requested_groups:
        requested_set = set(requested_groups)

        def row_matches(groups_text):
            groups = set(str(groups_text).split(","))
            return bool(groups.intersection(requested_set))

        selected_df = selected_df[selected_df["dashboard_groups"].apply(row_matches)].copy()

    selected_df["data_type_cd_lower"] = selected_df["data_type_cd"].astype(str).str.lower()
    selected_df["download_supported"] = selected_df["data_type_cd_lower"].isin(SUPPORTED_DOWNLOAD_DATA_TYPES)

    return selected_df


def get_location_details(station_ids):
    params = {
        "format": "rdb",
        "sites": ",".join(station_ids),
        "siteOutput": "expanded",
        "siteStatus": "all",
    }
    response = request_get(ENDPOINTS["site"], params=params)
    return parse_rdb(response.text)


def get_first_code_value(code_list):
    if isinstance(code_list, list) and len(code_list) > 0:
        item = code_list[0]
        if isinstance(item, dict):
            return item.get("value", "")
        return str(item)
    return ""


def parse_waterml_json(json_data, requested_metadata):
    records = []
    value_block = json_data.get("value", {})
    time_series_list = value_block.get("timeSeries", [])

    for ts in time_series_list:
        source_info = ts.get("sourceInfo", {})
        variable = ts.get("variable", {})

        site_no = get_first_code_value(source_info.get("siteCode", []))
        station_nm = source_info.get("siteName", "")

        variable_code = get_first_code_value(variable.get("variableCode", []))
        variable_name = variable.get("variableName", "")
        variable_description = variable.get("variableDescription", "")

        unit = ""
        if isinstance(variable.get("unit"), dict):
            unit = variable["unit"].get("unitAbbreviation", "") or variable["unit"].get("unitCode", "")

        stat_cd_from_json = ""
        stat_name_from_json = ""
        options = variable.get("options", {})
        if isinstance(options, dict):
            option_list = options.get("option", [])
            if isinstance(option_list, list) and len(option_list) > 0:
                stat_cd_from_json = option_list[0].get("optionCode", "")
                stat_name_from_json = option_list[0].get("value", "")

        values_groups = ts.get("values", [])
        for group in values_groups:
            values = group.get("value", [])
            for item in values:
                dt_raw = item.get("dateTime", "")
                val = item.get("value", "")
                qualifiers = item.get("qualifiers", "")
                if isinstance(qualifiers, list):
                    qualifiers = ",".join([str(q) for q in qualifiers])

                records.append({
                    "site_no": site_no,
                    "station_nm": station_nm,
                    "datetime_raw": dt_raw,
                    "value": val,
                    "unit": unit,
                    "variable_code": variable_code,
                    "variable_name": variable_name,
                    "variable_description": variable_description,
                    "stat_cd_json": stat_cd_from_json,
                    "stat_name_json": stat_name_from_json,
                    "qualifiers": qualifiers,
                    **requested_metadata,
                })

    df = pd.DataFrame(records)
    if df.empty:
        return df

    df["datetime_utc"] = pd.to_datetime(df["datetime_raw"], errors="coerce", utc=True).dt.tz_localize(None)
    df["datetime"] = df["datetime_utc"]
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.sort_values(["site_no", "datetime"]).reset_index(drop=True)
    return make_excel_safe(df)


def build_download_request(row, start_date, end_date):
    site_no = normalize_blank(row.get("site_no", ""))
    data_type_cd = normalize_blank(row.get("data_type_cd", "")).lower()
    parm_cd = normalize_blank(row.get("parm_cd", ""))
    stat_cd = normalize_blank(row.get("stat_cd", ""))

    if data_type_cd in {"iv", "uv", "rt"}:
        endpoint = ENDPOINTS["iv"]
        params = {
            "format": "json",
            "sites": site_no,
            "parameterCd": parm_cd,
            "startDT": start_date,
            "endDT": end_date,
            "siteStatus": "all",
        }

    elif data_type_cd == "dv":
        endpoint = ENDPOINTS["dv"]
        params = {
            "format": "json",
            "sites": site_no,
            "parameterCd": parm_cd,
            "startDT": start_date,
            "endDT": end_date,
            "siteStatus": "all",
        }
        if stat_cd:
            params["statCd"] = stat_cd

    elif data_type_cd == "gw":
        endpoint = ENDPOINTS["gwlevels"]
        params = {
            "format": "json",
            "sites": site_no,
            "startDT": start_date,
            "endDT": end_date,
            "siteStatus": "all",
        }
        if parm_cd:
            params["parameterCd"] = parm_cd

    else:
        return None, None

    return endpoint, params


def download_one_exact_series(row, start_date, end_date):
    endpoint, params = build_download_request(row, start_date, end_date)

    if endpoint is None:
        return pd.DataFrame(), "", "UNSUPPORTED_DATA_TYPE_IN_THIS_APP"

    response = request_get(endpoint, params=params, allow_404=True)

    if response.status_code == 404:
        return pd.DataFrame(), response.url, "NO_DATA_FOR_THIS_DATE_RANGE"

    try:
        json_data = response.json()
    except Exception as exc:
        return pd.DataFrame(), response.url, f"JSON_PARSE_ERROR: {exc}"

    metadata = {
        "requested_data_type_cd": normalize_blank(row.get("data_type_cd", "")),
        "requested_parm_cd": normalize_blank(row.get("parm_cd", "")),
        "requested_stat_cd": normalize_blank(row.get("stat_cd", "")),
        "requested_dashboard_groups": normalize_blank(row.get("dashboard_groups", "")),
        "period_begin_date": normalize_blank(row.get("begin_date", "")),
        "period_end_date": normalize_blank(row.get("end_date", "")),
        "period_count_nu": normalize_blank(row.get("count_nu", "")),
    }

    df = parse_waterml_json(json_data, metadata)
    if df.empty:
        return df, response.url, "EMPTY_RESPONSE"

    return df, response.url, "DOWNLOADED"


def run_downloads(selected_df, output_dir, start_date, end_date):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timeseries_dir = output_dir / "time_series_excels"
    timeseries_dir.mkdir(parents=True, exist_ok=True)

    selected_df = selected_df.copy()
    selected_df["data_type_cd_lower"] = selected_df["data_type_cd"].astype(str).str.lower()
    download_df = selected_df[selected_df["data_type_cd_lower"].isin(SUPPORTED_DOWNLOAD_DATA_TYPES)].copy()

    log_rows = []

    if download_df.empty:
        return pd.DataFrame([{
            "status": "NO_SUPPORTED_SERIES_SELECTED",
            "message": "No selected series can be downloaded by this app.",
        }])

    progress_bar = st.progress(0)
    status_box = st.empty()
    total_rows = len(download_df)
    done_rows = 0

    for site_no, site_rows in download_df.groupby("site_no"):
        site_file = timeseries_dir / f"USGS_{safe_name(site_no, 60)}_{start_date}_to_{end_date}.xlsx"
        used_sheet_names = set()

        with pd.ExcelWriter(site_file, engine="openpyxl") as writer:
            selected_sheet = make_unique_sheet_name("selected_series", used_sheet_names)
            make_excel_safe(site_rows).to_excel(writer, sheet_name=selected_sheet, index=False)

            for _, row in site_rows.iterrows():
                data_type_cd = normalize_blank(row.get("data_type_cd", "")).lower()
                parm_cd = normalize_blank(row.get("parm_cd", ""))
                stat_cd = normalize_blank(row.get("stat_cd", ""))

                status_box.info(
                    f"Downloading site={site_no} | "
                    f"data_type={data_type_cd} | "
                    f"parameter={parm_cd} | "
                    f"stat={stat_cd if stat_cd else 'none'}"
                )

                ts_df, used_url, status = download_one_exact_series(row=row, start_date=start_date, end_date=end_date)

                base_sheet_name = f"{data_type_cd}_{parm_cd}_{stat_cd if stat_cd else 'none'}"
                sheet_name = make_unique_sheet_name(base_sheet_name, used_sheet_names)

                if ts_df.empty:
                    no_data_df = pd.DataFrame({
                        "site_no": [site_no],
                        "data_type_cd": [data_type_cd],
                        "parm_cd": [parm_cd],
                        "stat_cd": [stat_cd],
                        "status": [status],
                        "used_url": [used_url],
                    })
                    make_excel_safe(no_data_df).to_excel(writer, sheet_name=sheet_name, index=False)

                else:
                    ts_df = make_excel_safe(ts_df)
                    ts_df.to_excel(writer, sheet_name=sheet_name, index=False)

                    minimal_cols = [
                        "datetime", "datetime_raw", "datetime_utc", "value", "unit",
                        "variable_code", "variable_name", "requested_data_type_cd",
                        "requested_parm_cd", "requested_stat_cd",
                    ]
                    minimal_cols = [c for c in minimal_cols if c in ts_df.columns]

                    minimal_sheet = make_unique_sheet_name(f"min_{base_sheet_name}", used_sheet_names)
                    make_excel_safe(ts_df[minimal_cols]).to_excel(writer, sheet_name=minimal_sheet, index=False)

                log_rows.append({
                    "site_no": site_no,
                    "station_nm": normalize_blank(row.get("station_nm", "")),
                    "data_type_cd": data_type_cd,
                    "parm_cd": parm_cd,
                    "stat_cd": stat_cd,
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": status,
                    "rows": len(ts_df),
                    "output_file": str(site_file.resolve()),
                    "used_url": used_url,
                })

                done_rows += 1
                progress_bar.progress(done_rows / total_rows)
                time.sleep(0.3)

    log_df = make_excel_safe(pd.DataFrame(log_rows))
    log_path = output_dir / "04_download_log.xlsx"
    log_df.to_excel(log_path, index=False)

    status_box.success("Download finished.")
    return log_df


st.set_page_config(
    page_title="USGS Data Downloader",
    page_icon="🌊",
    layout="wide",
)

st.title("USGS Station Data Downloader")
st.caption("Select USGS stations, inspect available data, then download time series for your selected date range.")

with st.sidebar:
    st.header("User Inputs")

    station_text = st.text_area(
        "USGS station IDs",
        value="453027099505001\n453358098260101\n451605097071701",
        height=160,
        help="Enter one USGS station ID per line. You can also paste dashboard text containing the station number.",
    )

    requested_groups = st.multiselect(
        "Requested data groups",
        options=DASHBOARD_GROUP_OPTIONS,
        default=["groundwater_level"],
    )

    output_dir = st.text_input(
        "Output folder",
        value=str(Path.cwd() / "outputs"),
    )

    start_date_value = st.date_input(
        "Start date",
        value=date(2000, 1, 1),
    )

    end_date_value = st.date_input(
        "End date",
        value=date.today(),
    )

    discover_button = st.button("1) Discover available station data", use_container_width=True)
    download_button = st.button("2) Download selected data", use_container_width=True)

    render_contact_section()


station_ids = [clean_site_id(line) for line in station_text.splitlines() if clean_site_id(line)]

if not station_ids:
    st.warning("Enter at least one valid USGS station ID.")
    st.stop()

st.subheader("Selected station IDs")
st.write(station_ids)


if discover_button:
    if not requested_groups:
        st.error("Select at least one data group.")
        st.stop()

    try:
        with st.spinner("Getting exact available series from USGS..."):
            inventory_df = discover_available_series(station_ids)
            selected_df = select_requested_series(inventory_df, requested_groups)

        with st.spinner("Getting station location details..."):
            location_df = get_location_details(station_ids)

        st.session_state["inventory_df"] = inventory_df
        st.session_state["selected_df"] = selected_df
        st.session_state["location_df"] = location_df

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        inventory_file = output_path / "01_exact_available_series_period_of_record.xlsx"
        selected_file = output_path / "02_selected_series.xlsx"
        location_file = output_path / "03_location_details_and_information.xlsx"

        make_excel_safe(inventory_df).to_excel(inventory_file, index=False)
        make_excel_safe(selected_df).to_excel(selected_file, index=False)
        make_excel_safe(location_df).to_excel(location_file, index=False)

        st.success("Station discovery completed.")

    except Exception as exc:
        st.error(f"Discovery failed: {exc}")


if "selected_df" in st.session_state:
    inventory_df = st.session_state["inventory_df"]
    selected_df = st.session_state["selected_df"]
    location_df = st.session_state["location_df"]

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Stations", len(station_ids))
    with col2:
        st.metric("All available series", len(inventory_df))
    with col3:
        st.metric("Selected series", len(selected_df))
    with col4:
        supported_count = int(selected_df["download_supported"].sum()) if "download_supported" in selected_df.columns else 0
        st.metric("Download-supported series", supported_count)

    st.subheader("Selected available data series")

    show_cols = [
        "site_no", "station_nm", "site_tp_cd", "dashboard_groups", "data_type_cd",
        "parm_cd", "stat_cd", "begin_date", "end_date", "count_nu", "download_supported",
    ]

    show_cols = [c for c in show_cols if c in selected_df.columns]
    st.dataframe(selected_df[show_cols], use_container_width=True)

    unsupported_df = selected_df[selected_df["download_supported"] == False] if "download_supported" in selected_df.columns else pd.DataFrame()

    if not unsupported_df.empty:
        st.warning(
            "Some selected series are listed by USGS but are not downloaded by this app. "
            "This version downloads iv, uv, rt, dv, and gw data types."
        )

    st.subheader("Station location details")

    location_cols = [
        "agency_cd", "site_no", "station_nm", "site_tp_cd", "dec_lat_va",
        "dec_long_va", "dec_coord_datum_cd", "alt_va", "alt_datum_cd",
        "huc_cd", "state_cd", "county_cd", "tz_cd", "well_depth_va",
        "hole_depth_va", "aqfr_cd", "aqfr_type_cd",
    ]

    location_cols = [c for c in location_cols if c in location_df.columns]
    st.dataframe(location_df[location_cols], use_container_width=True)

    if {"dec_lat_va", "dec_long_va"}.issubset(location_df.columns):
        map_df = location_df.copy()
        map_df["lat"] = pd.to_numeric(map_df["dec_lat_va"], errors="coerce")
        map_df["lon"] = pd.to_numeric(map_df["dec_long_va"], errors="coerce")
        map_df = map_df.dropna(subset=["lat", "lon"])

        if not map_df.empty:
            st.subheader("Station map")
            st.map(map_df[["lat", "lon"]])

    st.subheader("Download date range")
    st.write(f"Start date: `{start_date_value}`")
    st.write(f"End date: `{end_date_value}`")

    if download_button:
        if start_date_value > end_date_value:
            st.error("Start date must be before or equal to end date.")
            st.stop()

        try:
            with st.spinner("Downloading selected time series..."):
                log_df = run_downloads(
                    selected_df=selected_df,
                    output_dir=output_dir,
                    start_date=str(start_date_value),
                    end_date=str(end_date_value),
                )

            st.success("All downloads finished.")
            st.subheader("Download log")
            st.dataframe(log_df, use_container_width=True)

            st.info(f"Output folder: {Path(output_dir).resolve()}")

        except Exception as exc:
            st.error(f"Download failed: {exc}")

else:
    st.info("First click `Discover available station data` from the sidebar.")
