import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path("/opt/airflow")
DATA_DIR = PROJECT_ROOT / "data"

SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"


def read_silver_table(table_name: str) -> pd.DataFrame:
    file_path = SILVER_DIR / table_name / "data.parquet"

    if not file_path.exists():
        raise FileNotFoundError(f"Tabela silver não encontrada: {file_path}")

    return pd.read_parquet(file_path)


def write_gold_table(df: pd.DataFrame, table_name: str) -> None:
    output_dir = GOLD_DIR / table_name
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "data.parquet"

    # Idempotência simples: sobrescreve a tabela gold inteira.
    df.to_parquet(output_file, index=False)

    print(f"[GOLD] {table_name} -> {output_file} ({len(df)} linhas)")


def build_dim_cliente(customers: pd.DataFrame) -> pd.DataFrame:
    dim = customers[
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ]
    ].drop_duplicates(subset=["customer_id"])

    return dim


def build_dim_produto(products: pd.DataFrame, translation: pd.DataFrame | None = None) -> pd.DataFrame:
    cols = [
        "product_id",
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]

    existing_cols = [col for col in cols if col in products.columns]

    dim = products[existing_cols].drop_duplicates(subset=["product_id"])

    if translation is not None and "product_category_name" in dim.columns:
        dim = dim.merge(
            translation,
            on="product_category_name",
            how="left",
        )

    return dim


def build_dim_tempo(orders: pd.DataFrame) -> pd.DataFrame:
    dates = pd.to_datetime(orders["order_purchase_timestamp"], errors="coerce").dropna()

    dim = pd.DataFrame({"data": dates.dt.date.unique()})
    dim["data"] = pd.to_datetime(dim["data"])

    dim["ano"] = dim["data"].dt.year
    dim["mes"] = dim["data"].dt.month
    dim["dia"] = dim["data"].dt.day
    dim["ano_mes"] = dim["data"].dt.strftime("%Y-%m")
    dim["dia_semana"] = dim["data"].dt.day_name()
    dim["trimestre"] = dim["data"].dt.quarter

    return dim.sort_values("data")


def build_fato_pedidos(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    payments: pd.DataFrame,
    reviews: pd.DataFrame,
) -> pd.DataFrame:
    payments_agg = (
        payments
        .groupby("order_id", as_index=False)
        .agg(
            payment_value=("payment_value", "sum"),
            payment_installments=("payment_installments", "max"),
            payment_types=("payment_type", lambda x: ", ".join(sorted(set(x.dropna().astype(str)))))
        )
    )

    items_agg = (
        order_items
        .groupby("order_id", as_index=False)
        .agg(
            product_id=("product_id", "first"),
            seller_id=("seller_id", "first"),
            qtd_itens=("order_item_id", "count"),
            valor_produtos=("price", "sum"),
            valor_frete=("freight_value", "sum"),
        )
    )

    reviews_agg = (
        reviews
        .groupby("order_id", as_index=False)
        .agg(
            review_score=("review_score", "mean"),
        )
    )

    fato = (
        orders
        .merge(items_agg, on="order_id", how="left")
        .merge(payments_agg, on="order_id", how="left")
        .merge(reviews_agg, on="order_id", how="left")
    )

    fato["data_pedido"] = pd.to_datetime(
        fato["order_purchase_timestamp"],
        errors="coerce",
    ).dt.date

    fato["data_pedido"] = pd.to_datetime(fato["data_pedido"])

    fato["entregue_com_atraso"] = (
        pd.to_datetime(fato["order_delivered_customer_date"], errors="coerce")
        > pd.to_datetime(fato["order_estimated_delivery_date"], errors="coerce")
    )

    fato["tempo_entrega_dias"] = (
        pd.to_datetime(fato["order_delivered_customer_date"], errors="coerce")
        - pd.to_datetime(fato["order_purchase_timestamp"], errors="coerce")
    ).dt.days

    selected_cols = [
        "order_id",
        "customer_id",
        "product_id",
        "seller_id",
        "data_pedido",
        "order_status",
        "qtd_itens",
        "valor_produtos",
        "valor_frete",
        "payment_value",
        "payment_installments",
        "payment_types",
        "review_score",
        "entregue_com_atraso",
        "tempo_entrega_dias",
    ]

    existing_cols = [col for col in selected_cols if col in fato.columns]

    fato = fato[existing_cols].drop_duplicates(subset=["order_id"])

    return fato


def main():
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    orders = read_silver_table("olist_orders_dataset")
    customers = read_silver_table("olist_customers_dataset")
    products = read_silver_table("olist_products_dataset")
    order_items = read_silver_table("olist_order_items_dataset")
    payments = read_silver_table("olist_order_payments_dataset")
    reviews = read_silver_table("olist_order_reviews_dataset")

    try:
        translation = read_silver_table("olist_product_category_name_translation")
    except FileNotFoundError:
        translation = None

    dim_cliente = build_dim_cliente(customers)
    dim_produto = build_dim_produto(products, translation)
    dim_tempo = build_dim_tempo(orders)
    fato_pedidos = build_fato_pedidos(orders, order_items, payments, reviews)

    write_gold_table(dim_cliente, "dim_cliente")
    write_gold_table(dim_produto, "dim_produto")
    write_gold_table(dim_tempo, "dim_tempo")
    write_gold_table(fato_pedidos, "fato_pedidos")

    print("[GOLD] Camada gold gerada com sucesso")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Erro na transformação gold: {exc}", file=sys.stderr)
        raise
