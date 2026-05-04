from pathlib import Path
import duckdb


PROJECT_ROOT = Path("/opt/airflow")
DATA_DIR = PROJECT_ROOT / "data"
GOLD_DIR = DATA_DIR / "gold"

DUCKDB_FILE = GOLD_DIR / "olist_analytics.duckdb"


def main():
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DUCKDB_FILE))

    con.execute(f"""
    CREATE OR REPLACE VIEW fato_pedidos AS
    SELECT *
    FROM read_parquet('{GOLD_DIR}/fato_pedidos/data.parquet')
    """)

    con.execute(f"""
    CREATE OR REPLACE VIEW dim_cliente AS
    SELECT *
    FROM read_parquet('{GOLD_DIR}/dim_cliente/data.parquet')
    """)

    con.execute(f"""
    CREATE OR REPLACE VIEW dim_produto AS
    SELECT *
    FROM read_parquet('{GOLD_DIR}/dim_produto/data.parquet')
    """)

    con.execute(f"""
    CREATE OR REPLACE VIEW dim_tempo AS
    SELECT *
    FROM read_parquet('{GOLD_DIR}/dim_tempo/data.parquet')
    """)

    con.execute("""
    CREATE OR REPLACE VIEW vw_receita_mensal AS
    SELECT
        strftime(data_pedido, '%Y-%m') AS ano_mes,
        ROUND(SUM(payment_value), 2) AS receita,
        COUNT(DISTINCT order_id) AS total_pedidos,
        ROUND(SUM(payment_value) / COUNT(DISTINCT order_id), 2) AS ticket_medio
    FROM fato_pedidos
    GROUP BY 1
    ORDER BY 1
    """)

    con.execute("""
    CREATE OR REPLACE VIEW vw_top_categorias AS
    SELECT
        COALESCE(p.product_category_name_english, p.product_category_name) AS categoria,
        ROUND(SUM(f.payment_value), 2) AS receita,
        COUNT(DISTINCT f.order_id) AS total_pedidos
    FROM fato_pedidos f
    LEFT JOIN dim_produto p
        ON f.product_id = p.product_id
    GROUP BY 1
    ORDER BY receita DESC
    """)

    con.execute("""
    CREATE OR REPLACE VIEW vw_entrega_por_estado AS
    SELECT
        c.customer_state AS estado,
        ROUND(AVG(f.tempo_entrega_dias), 2) AS tempo_medio_entrega_dias,
        COUNT(DISTINCT f.order_id) AS total_pedidos
    FROM fato_pedidos f
    LEFT JOIN dim_cliente c
        ON f.customer_id = c.customer_id
    WHERE f.tempo_entrega_dias IS NOT NULL
    GROUP BY 1
    ORDER BY tempo_medio_entrega_dias DESC
    """)

    con.execute("""
    CREATE OR REPLACE VIEW vw_pedidos_atrasados AS
    SELECT
        ROUND(
            100.0 * SUM(CASE WHEN entregue_com_atraso THEN 1 ELSE 0 END)
            / COUNT(*),
            2
        ) AS percentual_pedidos_atrasados,
        COUNT(*) AS total_pedidos,
        SUM(CASE WHEN entregue_com_atraso THEN 1 ELSE 0 END) AS pedidos_atrasados
    FROM fato_pedidos
    """)

    con.execute("""
    CREATE OR REPLACE VIEW vw_reviews AS
    SELECT
        review_score,
        COUNT(DISTINCT order_id) AS total_pedidos
    FROM fato_pedidos
    WHERE review_score IS NOT NULL
    GROUP BY 1
    ORDER BY 1
    """)

    con.close()

    print(f"DuckDB criado com sucesso em: {DUCKDB_FILE}")


if __name__ == "__main__":
    main()
