-- KPI 1: Receita e pedidos por mês
SELECT
    strftime(data_pedido, '%Y-%m') AS ano_mes,
    ROUND(SUM(payment_value), 2) AS receita,
    COUNT(DISTINCT order_id) AS total_pedidos,
    ROUND(SUM(payment_value) / COUNT(DISTINCT order_id), 2) AS ticket_medio
FROM read_parquet('/opt/airflow/data/gold/fato_pedidos/data.parquet')
GROUP BY 1
ORDER BY 1;


-- KPI 2: Top 10 categorias por receita
SELECT
    COALESCE(p.product_category_name_english, p.product_category_name) AS categoria,
    ROUND(SUM(f.payment_value), 2) AS receita,
    COUNT(DISTINCT f.order_id) AS total_pedidos
FROM read_parquet('/opt/airflow/data/gold/fato_pedidos/data.parquet') f
LEFT JOIN read_parquet('/opt/airflow/data/gold/dim_produto/data.parquet') p
    ON f.product_id = p.product_id
GROUP BY 1
ORDER BY receita DESC
LIMIT 10;


-- KPI 3: Tempo médio de entrega por estado
SELECT
    c.customer_state AS estado,
    ROUND(AVG(f.tempo_entrega_dias), 2) AS tempo_medio_entrega_dias,
    COUNT(DISTINCT f.order_id) AS total_pedidos
FROM read_parquet('/opt/airflow/data/gold/fato_pedidos/data.parquet') f
LEFT JOIN read_parquet('/opt/airflow/data/gold/dim_cliente/data.parquet') c
    ON f.customer_id = c.customer_id
WHERE f.tempo_entrega_dias IS NOT NULL
GROUP BY 1
ORDER BY tempo_medio_entrega_dias DESC;


-- KPI 4: Percentual de pedidos atrasados
SELECT
    ROUND(
        100.0 * SUM(CASE WHEN entregue_com_atraso THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS percentual_pedidos_atrasados
FROM read_parquet('/opt/airflow/data/gold/fato_pedidos/data.parquet');


-- KPI 5: Distribuição de reviews
SELECT
    review_score,
    COUNT(DISTINCT order_id) AS total_pedidos
FROM read_parquet('/opt/airflow/data/gold/fato_pedidos/data.parquet')
WHERE review_score IS NOT NULL
GROUP BY 1
ORDER BY 1;
