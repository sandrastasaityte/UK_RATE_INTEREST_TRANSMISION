import pandas as pd
from pathlib import Path


def create_indicator_summary(
    df: pd.DataFrame,
    output_path: Path
):

    rows = []

    indicators = [
        "Bank_Rate",
        "CPI_Inflation",
        "GDP_Growth",
        "Investment_Growth",
        "Consumption_Growth",
        "Unemployment"
    ]

    for indicator in indicators:

        if indicator not in df.columns:
            continue

        series = df[indicator].dropna()

        if series.empty:
            continue

        rows.append({
            "Indicator": indicator,
            "Latest": series.iloc[-1],
            "Previous": (
                series.iloc[-2]
                if len(series) > 1
                else None
            ),
            "Mean": series.mean(),
            "Minimum": series.min(),
            "Maximum": series.max()
        })

    summary = pd.DataFrame(rows)

    summary.to_csv(
        output_path,
        index=False
    )

    return summary