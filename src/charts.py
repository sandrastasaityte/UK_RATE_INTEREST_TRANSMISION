import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path


def plot_interest_rate(
    df: pd.DataFrame,
    output_path: Path
):

    plt.figure(figsize=(12, 6))

    plt.plot(
        df.index,
        df["Bank_Rate"],
        label="Bank Rate"
    )

    plt.title(
        "UK Bank Rate"
    )

    plt.xlabel("Date")
    plt.ylabel("Percent")

    plt.grid(True)
    plt.legend()

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=300
    )

    plt.close()


def plot_gdp_interest_rate(
    df: pd.DataFrame,
    output_path: Path
):

    fig, ax1 = plt.subplots(
        figsize=(12, 6)
    )

    ax1.plot(
        df.index,
        df["GDP_Growth"],
        label="GDP Growth"
    )

    ax1.set_ylabel(
        "GDP Growth (%)"
    )

    ax2 = ax1.twinx()

    ax2.plot(
        df.index,
        df["Bank_Rate"],
        label="Bank Rate"
    )

    ax2.set_ylabel(
        "Bank Rate (%)"
    )

    plt.title(
        "UK Interest Rate and GDP Growth"
    )

    fig.tight_layout()

    plt.savefig(
        output_path,
        dpi=300
    )

    plt.close()


def plot_inflation(
    df: pd.DataFrame,
    output_path: Path
):

    plt.figure(figsize=(12, 6))

    plt.plot(
        df.index,
        df["CPI_Inflation"],
        label="CPI Inflation"
    )

    plt.axhline(
        2,
        linestyle="--",
        label="2% Target"
    )

    plt.title(
        "UK CPI Inflation"
    )

    plt.ylabel("Percent")

    plt.grid(True)
    plt.legend()

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=300
    )

    plt.close()