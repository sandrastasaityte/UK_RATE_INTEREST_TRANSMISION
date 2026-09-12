from pathlib import Path

from src.data_loader import (
    build_master_dataset,
    save_data
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

RAW_DIR = (
    PROJECT_DIR /
    "data" /
    "raw"
)

PROCESSED_DIR = (
    PROJECT_DIR /
    "data" /
    "processed"
)

OUTPUT_DIR = (
    PROJECT_DIR /
    "output"
)

RAW_DIR.mkdir(
    parents=True,
    exist_ok=True
)

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("UK INTEREST RATE TRANSMISSION")
    print("PROFESSIONAL UK MACROECONOMIC MODEL")
    print("=" * 80)

    print("\nOFFICIAL DATA SOURCES")
    print("-" * 80)
    print("Bank of England")
    print("Office for National Statistics")

    print("\nBuilding master dataset...")

    master = build_master_dataset()

    output_file = (
        PROCESSED_DIR /
        "uk_macro_data.csv"
    )

    save_data(
        master,
        output_file
    )

    print("\n" + "=" * 80)
    print("DATASET CREATED")
    print("=" * 80)

    print(
        f"\nObservations: {len(master):,}"
    )

    print(
        f"Start: {master['Date'].min().date()}"
    )

    print(
        f"End: {master['Date'].max().date()}"
    )

    print("\nVariables:")
    print(
        ", ".join(master.columns)
    )

    print("\nLatest observations:")

    print(
        master.tail(8).to_string(
            index=False
        )
    )

    print("\nMissing values:")

    print(
        master.isna()
        .sum()
        .to_string()
    )

    print("\n" + "=" * 80)
    print("REAL DATA PIPELINE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()