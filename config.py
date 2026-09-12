from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
TABLES_DIR = OUTPUT_DIR / "tables"
REPORTS_DIR = OUTPUT_DIR / "reports"

for directory in [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    CHARTS_DIR,
    TABLES_DIR,
    REPORTS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

START_DATE = "2000-01-01"