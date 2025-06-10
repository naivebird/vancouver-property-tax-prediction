import requests
import pandas as pd
from typing import List
from pathlib import Path

DATASET_URL = "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/property-tax-report/exports/parquet?lang=en&timezone=America%2FLos_Angeles"

def export_whole_dataset(output_path):
    response = requests.get(DATASET_URL)
    with open(output_path, "wb") as f:
        f.write(response.content)

def split_dataset(years: List[str], input_path: Path):
    df = pd.read_parquet(input_path)
    for year in years:
        df_year = df[df["tax_assessment_year"] == year]
        df_year.to_parquet(f"{input_path.parent}/property-tax-report-{year}.parquet")

def download_data(years, output_dir="data"):
    whole_dataset_path = Path(output_dir) / "property-tax-report.parquet"

    export_whole_dataset(whole_dataset_path)
    split_dataset(years, whole_dataset_path)

    whole_dataset_path.unlink()
    

if __name__ == "__main__":
    download_data(["2024", "2025"])
