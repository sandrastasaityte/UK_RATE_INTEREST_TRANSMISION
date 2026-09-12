from pathlib import Path


def generate_report(
    df,
    model,
    output_path: Path
):

    latest = df.iloc[-1]

    report = []

    report.append(
        "UK MONETARY POLICY TRANSMISSION REPORT"
    )

    report.append(
        "=" * 60
    )

    report.append("")
    report.append("1. EXECUTIVE SUMMARY")
    report.append("")

    if "Bank_Rate" in df.columns:

        report.append(
            f"Latest Bank Rate: "
            f"{latest['Bank_Rate']:.2f}%"
        )

    if "CPI_Inflation" in df.columns:

        report.append(
            f"CPI inflation: "
            f"{latest['CPI_Inflation']:.2f}%"
        )

    if "GDP_Growth" in df.columns:

        report.append(
            f"GDP growth: "
            f"{latest['GDP_Growth']:.2f}%"
        )

    report.append("")
    report.append("2. ECONOMIC TRANSMISSION")
    report.append("")

    report.append(
        "The monetary-policy transmission mechanism "
        "links the Bank Rate to financial conditions, "
        "household and corporate spending, aggregate "
        "demand and ultimately economic activity."
    )

    report.append("")
    report.append("3. ECONOMETRIC MODEL")
    report.append("")

    report.append(
        model.summary().as_text()
    )

    report.append("")
    report.append("4. ECONOMIST INTERPRETATION")
    report.append("")

    report.append(
        "A negative estimated coefficient on the "
        "interest rate would indicate an inverse "
        "statistical relationship between interest "
        "rates and GDP growth in the sample."
    )

    report.append(
        "The estimated relationship should not "
        "automatically be interpreted as a causal "
        "effect because monetary policy responds "
        "to economic conditions."
    )

    report.append("")
    report.append("5. CONCLUSION")
    report.append("")

    report.append(
        "The results should be interpreted together "
        "with inflation, labour-market conditions, "
        "financial conditions and the broader "
        "macroeconomic environment."
    )

    output_path.write_text(
        "\n".join(report),
        encoding="utf-8"
    )