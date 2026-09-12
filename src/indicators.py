import pandas as pd


def calculate_indicators(df):

    df = df.copy()

    df = df.sort_values(
        "Date"
    )

    # --------------------------------------------------------
    # Year-on-year growth
    # --------------------------------------------------------

    df["GDP_Growth"] = (
        df["GDP"]
        .pct_change(4)
        * 100
    )

    df["Consumption_Growth"] = (
        df["Consumption"]
        .pct_change(4)
        * 100
    )

    df["Investment_Growth"] = (
        df["Investment"]
        .pct_change(4)
        * 100
    )

    # --------------------------------------------------------
    # Monetary-policy variables
    # --------------------------------------------------------

    df["Bank_Rate_Change"] = (
        df["Bank_Rate"]
        .diff()
    )

    df["Real_Interest_Rate"] = (
        df["Bank_Rate"]
        - df["CPI"]
    )

    # --------------------------------------------------------
    # Lags
    # --------------------------------------------------------

    for lag in range(1, 5):

        df[
            f"Bank_Rate_Lag{lag}"
        ] = (
            df["Bank_Rate"]
            .shift(lag)
        )

        df[
            f"Bank_Rate_Change_Lag{lag}"
        ] = (
            df["Bank_Rate_Change"]
            .shift(lag)
        )

    return df