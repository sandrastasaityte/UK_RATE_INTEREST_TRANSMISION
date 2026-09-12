from pathlib import Path
import io
import re

import pandas as pd
import requests


# =============================================================================
# CONFIGURATION
# =============================================================================

START_DATE = "2000-01-01"

ONS_BASE_URL = "https://www.ons.gov.uk"

BOE_BASE_URL = "https://www.bankofengland.co.uk"

BOE_BANK_RATE_SERIES = "IUDBEDR"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}


# =============================================================================
# GENERAL HTTP REQUEST
# =============================================================================

def request_url(url, timeout=60, extra_headers=None):

    headers = HEADERS.copy()

    if extra_headers:
        headers.update(extra_headers)

    response = requests.get(
        url,
        headers=headers,
        timeout=timeout,
    )

    response.raise_for_status()

    return response


# =============================================================================
# ONS TABLE DISCOVERY
# =============================================================================

def find_ons_table(tables):

    candidates = []

    for table in tables:

        if table is None or table.empty:
            continue

        columns = [
            str(col).strip()
            for col in table.columns
        ]

        lower_columns = [
            col.lower()
            for col in columns
        ]

        has_period = any(
            col == "period"
            or "period" in col
            for col in lower_columns
        )

        has_value = any(
            col == "value"
            or "value" in col
            for col in lower_columns
        )

        if has_period and has_value:

            candidates.append(
                (
                    len(table),
                    table.copy(),
                )
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True,
    )

    return candidates[0][1]


# =============================================================================
# ONS DOWNLOAD
# =============================================================================

def download_ons_series(
    path,
    description,
    fallback_paths=None,
):

    print()
    print(f"Downloading ONS {description}...")

    if fallback_paths is None:
        fallback_paths = []

    candidate_paths = [
        path
    ] + fallback_paths

    # -------------------------------------------------------------------------
    # TRY GENERATOR
    # -------------------------------------------------------------------------

    for current_path in candidate_paths:

        generator_url = (
            f"{ONS_BASE_URL}/generator"
            f"?format=csv&uri={current_path}"
        )

        print()
        print("Trying ONS generator:")
        print(generator_url)

        try:

            response = request_url(
                generator_url,
                timeout=60,
            )

            raw = pd.read_csv(
                io.StringIO(
                    response.text
                )
            )

            print(
                "Generator columns:"
            )

            print(
                list(raw.columns)
            )

            period_column = find_period_column(raw)

            if period_column is not None:

                print(
                    "ONS generator returned observations."
                )

                return raw

            print(
                "ONS generator did not contain observations."
            )

        except requests.exceptions.HTTPError as exc:

            print(
                f"ONS generator unavailable: {exc}"
            )

        except Exception as exc:

            print(
                f"ONS generator parsing failed: {exc}"
            )

    # -------------------------------------------------------------------------
    # OFFICIAL ONS HTML FALLBACK
    # -------------------------------------------------------------------------

    print()
    print(
        "Falling back to official ONS time-series page..."
    )

    for current_path in candidate_paths:

        html_url = (
            f"{ONS_BASE_URL}{current_path}"
        )

        print(html_url)

        try:

            response = request_url(
                html_url,
                timeout=60,
            )

            tables = pd.read_html(
                io.StringIO(
                    response.text
                )
            )

            print(
                f"HTML tables found: {len(tables)}"
            )

            table = find_ons_table(
                tables
            )

            if table is not None:

                print(
                    "Selected ONS table:"
                )

                print(
                    list(table.columns)
                )

                print(
                    f"Rows returned: {len(table)}"
                )

                if len(table) > 0:

                    print()
                    print(
                        "Raw ONS table preview:"
                    )

                    print(
                        table.head().to_string(
                            index=False
                        )
                    )

                    return table

        except Exception as exc:

            print(
                f"HTML extraction failed: {exc}"
            )

    raise RuntimeError(
        f"Unable to retrieve ONS series: {description}"
    )


# =============================================================================
# FIND ONS PERIOD COLUMN
# =============================================================================

def find_period_column(df):

    for column in df.columns:

        name = str(
            column
        ).strip().lower()

        if name == "period":
            return column

        if "period" in name:
            return column

        if name in [
            "date",
            "time",
            "quarter",
            "month",
        ]:
            return column

    return None


# =============================================================================
# FIND ONS VALUE COLUMN
# =============================================================================

def find_value_column(df):

    for column in df.columns:

        name = str(
            column
        ).strip().lower()

        if name == "value":
            return column

        if "value" in name:
            return column

    numeric_columns = []

    for column in df.columns:

        converted = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        if converted.notna().sum() > 0:

            numeric_columns.append(
                column
            )

    if len(numeric_columns) == 1:

        return numeric_columns[0]

    return None


# =============================================================================
# PARSE ONS PERIOD
# =============================================================================

def parse_ons_period(value):

    if pd.isna(value):
        return pd.NaT

    text = str(
        value
    ).strip().upper()

    # -------------------------------------------------------------------------
    # QUARTER
    # -------------------------------------------------------------------------

    match = re.match(
        r"^(\d{4})\s*Q([1-4])$",
        text,
    )

    if match:

        year = int(
            match.group(1)
        )

        quarter = int(
            match.group(2)
        )

        month = {
            1: 3,
            2: 6,
            3: 9,
            4: 12,
        }[quarter]

        return pd.Timestamp(
            year=year,
            month=month,
            day=1,
        )

    # -------------------------------------------------------------------------
    # YEAR
    # -------------------------------------------------------------------------

    if re.match(
        r"^\d{4}$",
        text,
    ):

        return pd.Timestamp(
            year=int(text),
            month=1,
            day=1,
        )

    # -------------------------------------------------------------------------
    # MONTH
    # -------------------------------------------------------------------------

    month_match = re.match(
        r"^(\d{4})\s+([A-Z]{3})$",
        text,
    )

    if month_match:

        year = int(
            month_match.group(1)
        )

        month_text = month_match.group(2)

        month_map = {
            "JAN": 1,
            "FEB": 2,
            "MAR": 3,
            "APR": 4,
            "MAY": 5,
            "JUN": 6,
            "JUL": 7,
            "AUG": 8,
            "SEP": 9,
            "OCT": 10,
            "NOV": 11,
            "DEC": 12,
        }

        if month_text in month_map:

            return pd.Timestamp(
                year=year,
                month=month_map[month_text],
                day=1,
            )

    # -------------------------------------------------------------------------
    # GENERIC DATE
    # -------------------------------------------------------------------------

    try:

        return pd.to_datetime(
            text,
            errors="coerce",
        )

    except Exception:

        return pd.NaT


# =============================================================================
# CLEAN ONS SERIES
# =============================================================================

def clean_ons_series(
    raw,
    name,
):

    if raw is None:

        raise ValueError(
            f"ONS returned no data for {name}."
        )

    if raw.empty:

        raise ValueError(
            f"ONS returned empty data for {name}."
        )

    print()
    print(
        "Raw ONS columns:"
    )

    print(
        list(raw.columns)
    )

    period_column = find_period_column(
        raw
    )

    value_column = find_value_column(
        raw
    )

    print()
    print(
        f"Period column: {period_column}"
    )

    print(
        f"Value column: {value_column}"
    )

    if period_column is None:

        raise ValueError(
            f"Could not identify Period column for {name}."
        )

    if value_column is None:

        raise ValueError(
            f"Could not identify Value column for {name}."
        )

    data = raw[
        [
            period_column,
            value_column,
        ]
    ].copy()

    data.columns = [
        "Date",
        name,
    ]

    # -------------------------------------------------------------------------
    # DATE
    # -------------------------------------------------------------------------

    data["Date"] = (
        data["Date"]
        .apply(parse_ons_period)
    )

    # -------------------------------------------------------------------------
    # VALUE
    # -------------------------------------------------------------------------

    data[name] = (
        data[name]
        .astype(str)
        .str.replace(
            ",",
            "",
            regex=False,
        )
        .str.replace(
            "—",
            "",
            regex=False,
        )
        .str.replace(
            "–",
            "",
            regex=False,
        )
        .str.strip()
    )

    data[name] = pd.to_numeric(
        data[name],
        errors="coerce",
    )

    # -------------------------------------------------------------------------
    # REMOVE INVALID ROWS
    # -------------------------------------------------------------------------

    data = data.dropna(
        subset=[
            "Date",
            name,
        ]
    )

    # -------------------------------------------------------------------------
    # START DATE
    # -------------------------------------------------------------------------

    data = data[
        data["Date"]
        >= pd.Timestamp(
            START_DATE
        )
    ]

    # -------------------------------------------------------------------------
    # CLEAN
    # -------------------------------------------------------------------------

    data = (
        data
        .drop_duplicates(
            subset=["Date"]
        )
        .sort_values("Date")
        .reset_index(drop=True)
    )

    if data.empty:

        raise ValueError(
            f"ONS returned no usable observations for {name}."
        )

    print()
    print(
        f"{name}: {len(data)} observations"
    )

    print(
        f"Range: "
        f"{data['Date'].min().date()} "
        f"to "
        f"{data['Date'].max().date()}"
    )

    return data


# =============================================================================
# GDP
# =============================================================================

def get_gdp():

    raw = download_ons_series(
        path=(
            "/economy/grossdomesticproductgdp/"
            "timeseries/abmi/qna"
        ),
        description="GDP",
    )

    return clean_ons_series(
        raw,
        "GDP",
    )


# =============================================================================
# HOUSEHOLD CONSUMPTION
# =============================================================================

def get_consumption():

    raw = download_ons_series(
        path=(
            "/economy/nationalaccounts/"
            "satelliteaccounts/timeseries/abjr"
        ),
        description="household consumption",
        fallback_paths=[
            (
                "/economy/nationalaccounts/"
                "satelliteaccounts/timeseries/abjr/ct"
            ),
            (
                "/economy/nationalaccounts/"
                "satelliteaccounts/timeseries/abjr/pn2"
            ),
        ],
    )

    return clean_ons_series(
        raw,
        "Consumption",
    )


# =============================================================================
# INVESTMENT
# =============================================================================

def get_investment():

    raw = download_ons_series(
        path=(
            "/economy/grossdomesticproductgdp/"
            "timeseries/npqt"
        ),
        description="investment",
    )

    return clean_ons_series(
        raw,
        "Investment",
    )


# =============================================================================
# CPI
# =============================================================================

def get_cpi():

    raw = download_ons_series(
        path=(
            "/economy/inflationandpriceindices/"
            "timeseries/d7g7/mm23"
        ),
        description="CPI inflation",
        fallback_paths=[
            (
                "/economy/inflationandpriceindices/"
                "timeseries/d7g7"
            ),
        ],
    )

    return clean_ons_series(
        raw,
        "CPI",
    )


# =============================================================================
# UNEMPLOYMENT
# =============================================================================

def get_unemployment():

    raw = download_ons_series(
        path=(
            "/employmentandlabourmarket/"
            "peoplenotinwork/unemployment/"
            "timeseries/mgsx"
        ),
        description="unemployment",
        fallback_paths=[
            (
                "/employmentandlabourmarket/"
                "peoplenotinwork/unemployment/"
                "timeseries/mgsx/lms"
            ),
        ],
    )

    return clean_ons_series(
        raw,
        "Unemployment",
    )


# =============================================================================
# BANK OF ENGLAND BANK RATE
# =============================================================================

def get_bank_rate_history():

    print()
    print(
        "Downloading Bank of England Bank Rate..."
    )

    series_code = BOE_BANK_RATE_SERIES

    date_from = "01/Jan/2000"
    date_to = "now"

    csv_url = (
        f"{BOE_BASE_URL}/boeapps/database/"
        "_iadb-fromshowcolumns.asp"
        "?csv.x=yes"
        f"&Datefrom={date_from}"
        f"&Dateto={date_to}"
        f"&SeriesCodes={series_code}"
        "&CSVF=TN"
        "&UsingCodes=Y"
        "&VPD=Y"
        "&VFD=N"
    )

    print()
    print(
        "Bank of England CSV:"
    )

    print(
        csv_url
    )

    extra_headers = {
        "Referer": (
            f"{BOE_BASE_URL}/boeapps/database/"
        ),
        "Accept": (
            "text/csv,text/plain,"
            "application/octet-stream,*/*"
        ),
    }

    try:

        response = request_url(
            csv_url,
            timeout=60,
            extra_headers=extra_headers,
        )

    except Exception as exc:

        raise RuntimeError(
            "Unable to download Bank of England "
            f"Bank Rate series {series_code}: {exc}"
        )

    print()
    print(
        f"Bank of England response: "
        f"{response.status_code}"
    )

    raw_text = response.text

    if not raw_text.strip():

        raise RuntimeError(
            "Bank of England returned an empty CSV."
        )

    print()
    print(
        "Bank of England CSV preview:"
    )

    print(
        raw_text[:500]
    )

    # -------------------------------------------------------------------------
    # PARSE CSV
    # -------------------------------------------------------------------------

    try:

        data = pd.read_csv(
            io.StringIO(
                raw_text
            )
        )

    except Exception as exc:

        raise RuntimeError(
            "Could not parse Bank of England CSV: "
            f"{exc}"
        )

    print()
    print(
        "Bank of England CSV columns:"
    )

    print(
        list(data.columns)
    )

    if data.empty:

        raise RuntimeError(
            "Bank of England CSV contains no rows."
        )

    print()
    print(
        "Raw Bank Rate data:"
    )

    print(
        data.head().to_string(
            index=False
        )
    )

    # -------------------------------------------------------------------------
    # IDENTIFY DATE COLUMN
    # -------------------------------------------------------------------------

    date_column = None

    for column in data.columns:

        name = str(
            column
        ).strip().lower()

        if (
            name == "date"
            or "date" in name
        ):

            date_column = column

            break

    if date_column is None:

        date_column = data.columns[0]

    # -------------------------------------------------------------------------
    # IDENTIFY RATE COLUMN
    # -------------------------------------------------------------------------

    rate_column = None

    for column in data.columns:

        if column == date_column:
            continue

        name = str(
            column
        ).strip().upper()

        if (
            "IUDBEDR" in name
            or "RATE" in name
        ):

            rate_column = column

            break

    if rate_column is None:

        if len(data.columns) >= 2:

            rate_column = data.columns[1]

        else:

            raise RuntimeError(
                "Could not identify Bank Rate column."
            )

    print()
    print(
        f"Date column: {date_column}"
    )

    print(
        f"Rate column: {rate_column}"
    )

    # -------------------------------------------------------------------------
    # SELECT
    # -------------------------------------------------------------------------

    data = data[
        [
            date_column,
            rate_column,
        ]
    ].copy()

    data.columns = [
        "Date",
        "Bank_Rate",
    ]

    # -------------------------------------------------------------------------
    # DATE
    # -------------------------------------------------------------------------

    data["Date"] = pd.to_datetime(
        data["Date"],
        errors="coerce",
        dayfirst=True,
    )

    # -------------------------------------------------------------------------
    # RATE
    # -------------------------------------------------------------------------

    data["Bank_Rate"] = (
        data["Bank_Rate"]
        .astype(str)
        .str.replace(
            ",",
            "",
            regex=False,
        )
        .str.replace(
            "%",
            "",
            regex=False,
        )
        .str.strip()
    )

    data["Bank_Rate"] = pd.to_numeric(
        data["Bank_Rate"],
        errors="coerce",
    )

    # -------------------------------------------------------------------------
    # CLEAN
    # -------------------------------------------------------------------------

    data = data.dropna(
        subset=[
            "Date",
            "Bank_Rate",
        ]
    )

    data = data[
        data["Date"]
        >= pd.Timestamp(
            START_DATE
        )
    ]

    data = (
        data
        .sort_values("Date")
        .drop_duplicates(
            subset=["Date"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    if data.empty:

        raise RuntimeError(
            "Bank Rate dataset is empty after cleaning."
        )

    # -------------------------------------------------------------------------
    # VALIDATE
    # -------------------------------------------------------------------------

    if data["Bank_Rate"].isna().all():

        raise RuntimeError(
            "Bank Rate contains no usable numeric observations."
        )

    print()
    print(
        "=" * 80
    )

    print(
        "BANK OF ENGLAND BANK RATE SUCCESSFULLY LOADED"
    )

    print(
        "=" * 80
    )

    print()
    print(
        f"Series: {series_code}"
    )

    print(
        "Description: Official Bank Rate"
    )

    print(
        f"Observations: {len(data):,}"
    )

    print(
        f"Start: {data['Date'].min().date()}"
    )

    print(
        f"End: {data['Date'].max().date()}"
    )

    print()
    print(
        "Latest observations:"
    )

    print(
        data.tail(10).to_string(
            index=False
        )
    )

    return data


# =============================================================================
# DAILY BANK RATE → QUARTERLY
# =============================================================================

def build_daily_bank_rate():

    data = get_bank_rate_history()

    data = data.set_index(
        "Date"
    )

    # Quarterly average
    quarterly_average = (
        data["Bank_Rate"]
        .resample("QE")
        .mean()
        .rename(
            "Bank_Rate"
        )
    )

    # Quarter-end rate
    quarterly_end = (
        data["Bank_Rate"]
        .resample("QE")
        .last()
        .rename(
            "Bank_Rate_Quarter_End"
        )
    )

    quarterly = pd.concat(
        [
            quarterly_average,
            quarterly_end,
        ],
        axis=1,
    ).reset_index()

    quarterly["Date"] = (
        quarterly["Date"]
        .dt.to_period("Q")
        .dt.start_time
    )

    quarterly = quarterly[
        quarterly["Date"]
        >= pd.Timestamp(
            START_DATE
        )
    ]

    quarterly = (
        quarterly
        .sort_values("Date")
        .reset_index(drop=True)
    )

    return quarterly


# =============================================================================
# NORMALISE TO QUARTER START
# =============================================================================

def normalise_quarter_start(df):

    df = df.copy()

    df["Date"] = (
        pd.to_datetime(
            df["Date"]
        )
        .dt.to_period("Q")
        .dt.start_time
    )

    return df


# =============================================================================
# MERGE SERIES
# =============================================================================

def merge_series(
    left,
    right,
):

    left = normalise_quarter_start(
        left
    )

    right = normalise_quarter_start(
        right
    )

    merged = pd.merge(
        left,
        right,
        on="Date",
        how="outer",
    )

    return (
        merged
        .sort_values("Date")
        .reset_index(drop=True)
    )


# =============================================================================
# MONTHLY → QUARTERLY
# =============================================================================

def monthly_to_quarterly(
    df,
    value_column,
    method="mean",
):

    data = df.copy()

    data["Date"] = pd.to_datetime(
        data["Date"]
    )

    data = data.set_index(
        "Date"
    )

    if method == "mean":

        quarterly = (
            data[value_column]
            .resample("QE")
            .mean()
        )

    elif method == "last":

        quarterly = (
            data[value_column]
            .resample("QE")
            .last()
        )

    elif method == "sum":

        quarterly = (
            data[value_column]
            .resample("QE")
            .sum()
        )

    else:

        raise ValueError(
            f"Unknown aggregation method: {method}"
        )

    quarterly = (
        quarterly
        .to_frame()
        .reset_index()
    )

    quarterly["Date"] = (
        quarterly["Date"]
        .dt.to_period("Q")
        .dt.start_time
    )

    return quarterly


# =============================================================================
# BUILD MASTER DATASET
# =============================================================================

def build_master_dataset():

    print()
    print("=" * 80)
    print(
        "BUILDING UK MACROECONOMIC MASTER DATASET"
    )
    print("=" * 80)

    # =========================================================================
    # GDP
    # =========================================================================

    gdp = get_gdp()

    # =========================================================================
    # CONSUMPTION
    # =========================================================================

    consumption = get_consumption()

    # =========================================================================
    # INVESTMENT
    # =========================================================================

    investment = get_investment()

    # =========================================================================
    # CPI
    # =========================================================================

    cpi = get_cpi()

    # =========================================================================
    # UNEMPLOYMENT
    # =========================================================================

    unemployment = get_unemployment()

    # =========================================================================
    # BANK RATE
    # =========================================================================

    bank_rate = build_daily_bank_rate()

    # =========================================================================
    # CONVERT MONTHLY DATA TO QUARTERLY
    # =========================================================================

    cpi_quarterly = monthly_to_quarterly(
        cpi,
        "CPI",
        method="mean",
    )

    unemployment_quarterly = monthly_to_quarterly(
        unemployment,
        "Unemployment",
        method="mean",
    )

    # =========================================================================
    # MERGE DATA
    # =========================================================================

    master = gdp.copy()

    master = merge_series(
        master,
        consumption,
    )

    master = merge_series(
        master,
        investment,
    )

    master = merge_series(
        master,
        cpi_quarterly,
    )

    master = merge_series(
        master,
        unemployment_quarterly,
    )

    master = merge_series(
        master,
        bank_rate,
    )

    # =========================================================================
    # FINAL DATE
    # =========================================================================

    master["Date"] = pd.to_datetime(
        master["Date"]
    )

    master = master[
        master["Date"]
        >= pd.Timestamp(
            START_DATE
        )
    ]

    master = (
        master
        .sort_values("Date")
        .reset_index(drop=True)
    )

    # =========================================================================
    # NUMERIC CONVERSION
    # =========================================================================

    numeric_columns = [
        "GDP",
        "Consumption",
        "Investment",
        "CPI",
        "Unemployment",
        "Bank_Rate",
        "Bank_Rate_Quarter_End",
    ]

    for column in numeric_columns:

        if column in master.columns:

            master[column] = pd.to_numeric(
                master[column],
                errors="coerce",
            )

    # =========================================================================
    # VALIDATION
    # =========================================================================

    print()
    print("=" * 80)
    print(
        "MASTER DATASET VALIDATION"
    )
    print("=" * 80)

    print()
    print(
        f"Observations: {len(master):,}"
    )

    print(
        f"Start: {master['Date'].min().date()}"
    )

    print(
        f"End: {master['Date'].max().date()}"
    )

    print()
    print(
        "Variables:"
    )

    print(
        ", ".join(master.columns)
    )

    print()
    print(
        "Missing values:"
    )

    print(
        master.isna().sum().to_string()
    )

    print()
    print(
        "Latest observations:"
    )

    print(
        master.tail(8).to_string(
            index=False
        )
    )

    # =========================================================================
    # REQUIRED VARIABLES
    # =========================================================================

    required_columns = [
        "Date",
        "GDP",
        "Consumption",
        "Investment",
        "CPI",
        "Unemployment",
        "Bank_Rate",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in master.columns
    ]

    if missing_columns:

        raise RuntimeError(
            "Master dataset is missing required "
            f"variables: {missing_columns}"
        )

    # =========================================================================
    # SAMPLE SIZE
    # =========================================================================

    if len(master) < 60:

        raise RuntimeError(
            "Master dataset contains fewer than "
            "60 quarterly observations. "
            "Econometric analysis should not proceed."
        )

    # =========================================================================
    # CHECK CORE MISSING VALUES
    # =========================================================================

    core_columns = [
        "GDP",
        "Consumption",
        "Investment",
        "CPI",
        "Unemployment",
        "Bank_Rate",
    ]

    core_missing = (
        master[core_columns]
        .isna()
        .sum()
    )

    if core_missing.sum() > 0:

        print()
        print(
            "WARNING: Missing observations detected "
            "in core variables."
        )

        print(
            core_missing[
                core_missing > 0
            ].to_string()
        )

    print()
    print("=" * 80)
    print(
        "MASTER DATASET BUILD COMPLETE"
    )
    print("=" * 80)

    return master


# =============================================================================
# SAVE DATA
# =============================================================================

def save_data(
    df,
    output_file,
):

    output_file = Path(
        output_file
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        output_file,
        index=False,
    )

    print()
    print(
        "Saved master dataset:"
    )

    print(
        output_file
    )


# =============================================================================
# DIRECT TEST
# =============================================================================

if __name__ == "__main__":

    data = build_master_dataset()

    print()
    print("=" * 80)
    print(
        "DATA LOADER TEST COMPLETE"
    )
    print("=" * 80)

    print()

    print(
        data.tail(10).to_string(
            index=False
        )
    )