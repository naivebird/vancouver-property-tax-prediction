import requests
from pathlib import Path

DATASET_URL = "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/property-tax-report/exports/parquet?lang=en&timezone=America%2FLos_Angeles"

def download_data(output_dir=Path("data")):
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = output_dir / "property-tax-report.parquet"
    response = requests.get(DATASET_URL)
    with open(dataset_path, "wb") as f:
        f.write(response.content)

if __name__ == "__main__":
    download_data()
