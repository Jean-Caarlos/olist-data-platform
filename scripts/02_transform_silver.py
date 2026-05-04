import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path("/opt/airflow")
DATA_DIR = PROJECT_ROOT / "data"

BRONZE_OLIST_DIR = DATA_DIR / "bronze" / "olist"
BRONZE_API_DIR = DATA_DIR / "bronze" / "api_holidays"
SILVER_DIR = DATA_DIR / "silver"


DATE_COLUMNS = {
    "olist_orders_dataset": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "olist_order_reviews_dataset": [
        "review_creation_date",
        "review_answer_timestamp",
    ],
    "dim_feriados": [
        "date",
    ],
}


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return df


def read_latest_snapshot(table_dir: Path) -> pd.DataFrame:
    parquet_files = sorted(table_dir.glob("*.parquet"))

    if not parquet_files:
        raise FileNotFoundError(f"Nenhum parquet encontrado em {table_dir}")

    latest_file = parquet_files[-1]
    print(f"[SILVER] Lendo snapshot: {latest_file}")

    return pd.read_parquet(latest_file)


def write_silver_table(df: pd.DataFrame, table_name: str) -> None:
    output_dir = SILVER_DIR / table_name
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "data.parquet"
    df.to_parquet(output_file, index=False)

    print(f"[SILVER] {table_name} -> {output_file} ({len(df)} linhas)")


def transform_table(table_name: str, df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_column_names(df)
    df = df.drop_duplicates()

    for col in DATE_COLUMNS.get(table_name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype("string").str.strip()

    return df


def transform_olist_tables() -> None:
    if not BRONZE_OLIST_DIR.exists():
        raise FileNotFoundError(f"Diretório bronze não encontrado: {BRONZE_OLIST_DIR}")

    table_dirs = [p for p in BRONZE_OLIST_DIR.iterdir() if p.is_dir()]

    if not table_dirs:
        raise FileNotFoundError(f"Nenhuma tabela encontrada em {BRONZE_OLIST_DIR}")

    for table_dir in table_dirs:
        table_name = table_dir.name
        df = read_latest_snapshot(table_dir)
        df = transform_table(table_name, df)
        write_silver_table(df, table_name)


def transform_api_holidays() -> None:
    parquet_files = sorted(BRONZE_API_DIR.glob("*.parquet"))

    if not parquet_files:
        raise FileNotFoundError(f"Nenhum parquet encontrado em {BRONZE_API_DIR}")

    latest_file = parquet_files[-1]
    print(f"[SILVER] Lendo API holidays: {latest_file}")

    df = pd.read_parquet(latest_file)
    df = transform_table("dim_feriados", df)

    write_silver_table(df, "dim_feriados")


def main():
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    transform_olist_tables()
    transform_api_holidays()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Erro na transformação silver: {exc}", file=sys.stderr)
        raise
