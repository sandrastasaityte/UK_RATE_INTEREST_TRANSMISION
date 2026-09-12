import pandas as pd


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()

    data = data[~data.index.duplicated(keep="first")]
    data = data.sort_index()

    for column in data.columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    data = data.dropna(axis=1, how="all")

    return data


def calculate_growth(
    df: pd.DataFrame,
    column: str,
    periods: int = 4
) -> pd.Series:

    return df[column].pct_change(periods=periods) * 100