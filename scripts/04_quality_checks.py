import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path("/opt/airflow")
DATA_DIR = PROJECT_ROOT / "data"
SILVER_DIR = DATA_DIR / "silver"


REQUIRED_TABLES = [
    "olist_orders_dataset",
    "olist_customers_dataset",
    "olist_order_items_dataset",
    "olist_order_payments_dataset",
    "olist_products_dataset",
]


UNIQUE_KEY_CHECKS = {
    "olist_orders_dataset": "order_id",
    "olist_customers_dataset": "customer_id",
    "olist_products_dataset": "product_id",
}


def read_silver_table(table_name: str) -> pd.DataFrame:
    file_path = SILVER_DIR / table_name / "data.parquet"

    if not file_path.exists():
        raise FileNotFoundError(f"Tabela silver não encontrada: {file_path}")

    return pd.read_parquet(file_path)


def check_required_tables_exist() -> None:
    print("[DQ] Checando existência das tabelas obrigatórias")

    for table_name in REQUIRED_TABLES:
        file_path = SILVER_DIR / table_name / "data.parquet"

        if not file_path.exists():
            raise FileNotFoundError(f"Tabela obrigatória ausente: {file_path}")

        print(f"[DQ][OK] Existe: {table_name}")


def check_minimum_rows() -> None:
    print("[DQ] Checando contagem mínima de linhas")

    for table_name in REQUIRED_TABLES:
        df = read_silver_table(table_name)

        if len(df) == 0:
            raise ValueError(f"Tabela vazia: {table_name}")

        print(f"[DQ][OK] {table_name}: {len(df)} linhas")


def check_unique_keys() -> None:
    print("[DQ] Checando unicidade de chaves")

    for table_name, key_col in UNIQUE_KEY_CHECKS.items():
        df = read_silver_table(table_name)

        if key_col not in df.columns:
            raise ValueError(f"Coluna {key_col} não encontrada em {table_name}")

        duplicated_count = df[key_col].duplicated().sum()

        if duplicated_count > 0:
            raise ValueError(
                f"Chave duplicada em {table_name}.{key_col}: {duplicated_count} duplicatas"
            )

        print(f"[DQ][OK] {table_name}.{key_col} é único")


def check_payment_values() -> None:
    print("[DQ] Checando valores de pagamento")

    df = read_silver_table("olist_order_payments_dataset")

    if "payment_value" not in df.columns:
        raise ValueError("Coluna payment_value não encontrada em olist_order_payments_dataset")

    invalid_count = (df["payment_value"] < 0).sum()

    if invalid_count > 0:
        raise ValueError(f"Foram encontrados {invalid_count} pagamentos com valor negativo")

    print("[DQ][OK] payment_value sem valores negativos")


def main():
    check_required_tables_exist()
    check_minimum_rows()
    check_unique_keys()
    check_payment_values()

    print("[DQ] Todas as checagens passaram com sucesso")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Erro nas checagens de qualidade: {exc}", file=sys.stderr)
        raise
