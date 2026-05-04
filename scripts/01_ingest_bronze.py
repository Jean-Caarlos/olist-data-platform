import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import requests


PROJECT_ROOT = Path("/opt/airflow")
DATA_DIR = PROJECT_ROOT / "data"

RAW_OLIST_DIR = DATA_DIR / "raw" / "olist"
BRONZE_DIR = DATA_DIR / "bronze"

BRONZE_OLIST_DIR = BRONZE_DIR / "olist"
BRONZE_API_DIR = BRONZE_DIR / "api_holidays"


def ensure_dirs():
    BRONZE_OLIST_DIR.mkdir(parents=True, exist_ok=True)
    BRONZE_API_DIR.mkdir(parents=True, exist_ok=True)


def ingest_olist_csvs():
    csv_files = list(RAW_OLIST_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"Nenhum CSV encontrado em {RAW_OLIST_DIR}. "
            "Coloque os arquivos do dataset Olist nessa pasta."
        )

    ingestion_ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    for csv_file in csv_files:
        table_name = csv_file.stem
        output_dir = BRONZE_OLIST_DIR / table_name
        output_dir.mkdir(parents=True, exist_ok=True)

        df = pd.read_csv(csv_file)

        df["_source_file"] = csv_file.name
        df["_ingestion_ts"] = ingestion_ts

        output_file = output_dir / f"snapshot_{ingestion_ts}.parquet"
        df.to_parquet(output_file, index=False)

        print(f"[BRONZE][OLIST] {csv_file.name} -> {output_file} ({len(df)} linhas)")


def ingest_holidays_api():
    year = 2018
    url = f"https://brasilapi.com.br/api/feriados/v1/{year}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(data)
    df["_api_url"] = url
    df["_ingestion_ts"] = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    output_file = BRONZE_API_DIR / f"holidays_br_{year}.parquet"
    df.to_parquet(output_file, index=False)

    print(f"[BRONZE][API] {url} -> {output_file} ({len(df)} linhas)")


def main():
    ensure_dirs()
    ingest_olist_csvs()
    ingest_holidays_api()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Erro na ingestão bronze: {exc}", file=sys.stderr)
        raise
