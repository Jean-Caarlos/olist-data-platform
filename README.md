# Olist Data Platform

🇺🇸 English version first.  
🇧🇷 Versão em português após a versão em inglês.

---

# 🇺🇸 English Version

## 1. Overview

This project was developed as a practical data engineering challenge for a Mid-Level Data Engineer position.

The solution implements an end-to-end analytical data platform using the public Olist dataset, enriched with a public holidays API. The pipeline organizes data into Bronze, Silver, and Gold layers, applies data quality checks, builds a dimensional model, and delivers business indicators through an Apache Superset dashboard.

---

## 2. Goal

Build a local and reproducible analytical pipeline with:

- Ingestion of Olist CSV files.
- Ingestion of an additional public API source.
- Data organization into Bronze, Silver, and Gold layers.
- Transformations using Python/Pandas and DuckDB.
- Orchestration with Apache Airflow.
- Analytical storage in Parquet.
- Analytical querying with DuckDB.
- Visualization with Apache Superset.
- Local execution via Docker Compose.

---

## 3. Architecture

General flow:

~~~text
Olist CSVs + BrasilAPI
        |
        v
Bronze
        |
        v
Silver
        |
        v
Quality Checks
        |
        v
Gold - Dimensional Model
        |
        v
DuckDB Views
        |
        v
Apache Superset
~~~

Main components:

| Component | Purpose |
|---|---|
| Docker Compose | Runs the local environment |
| Airflow | Orchestrates the pipeline |
| Postgres | Airflow metadata database |
| MinIO | Local object storage available in the environment |
| Python/Pandas | Data ingestion, cleaning, and standardization |
| DuckDB | Analytical transformations, views, and Parquet queries |
| Parquet | Analytical format for the data layers |
| Superset | Business dashboard |

---

## 4. Data sources

### Main dataset

The project uses the public Brazilian E-Commerce Public Dataset by Olist, available on Kaggle.

Files used:

- `olist_orders_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_product_category_name_translation.csv`

### Additional API source

To satisfy the multiple-source requirement, the project uses the public BrasilAPI endpoint:

~~~text
https://brasilapi.com.br/api/feriados/v1/2018
~~~

Holiday data is ingested into Bronze and promoted to Silver as `dim_feriados`.

---

## 5. Data layers

### Bronze

Location:

~~~text
data/bronze/
~~~

Characteristics:

- Stores raw snapshots in Parquet.
- Keeps source metadata.
- Does not apply business rules.
- Preserves ingestion history using timestamps.

### Silver

Location:

~~~text
data/silver/
~~~

Transformations:

- Column name normalization.
- Date conversion.
- Duplicate removal.
- Text standardization.
- Initial handling of structural inconsistencies.

### Gold

Location:

~~~text
data/gold/
~~~

Generated tables:

- `fato_pedidos`
- `dim_cliente`
- `dim_produto`
- `dim_tempo`

The following DuckDB file is also generated:

~~~text
data/gold/olist_analytics.duckdb
~~~

This file contains the analytical views used by Superset.

---

## 6. Dimensional model

### `fato_pedidos`

Grain: one row per order.

| Field | Description |
|---|---|
| `order_id` | Order identifier |
| `customer_id` | Customer key |
| `product_id` | Main product in the order |
| `seller_id` | Main seller |
| `data_pedido` | Purchase date |
| `order_status` | Order status |
| `qtd_itens` | Number of items |
| `valor_produtos` | Product amount |
| `valor_frete` | Freight amount |
| `payment_value` | Paid amount |
| `review_score` | Average review score |
| `entregue_com_atraso` | Indicates whether the order was delayed |
| `tempo_entrega_dias` | Delivery time in days |

### `dim_cliente`

Grain: one row per `customer_id`.

Main fields:

- `customer_id`
- `customer_unique_id`
- `customer_zip_code_prefix`
- `customer_city`
- `customer_state`

### `dim_produto`

Grain: one row per `product_id`.

Main fields:

- `product_id`
- `product_category_name`
- `product_category_name_english`
- `product_weight_g`
- `product_length_cm`
- `product_height_cm`
- `product_width_cm`

### `dim_tempo`

Grain: one row per order date.

Main fields:

- `data`
- `ano`
- `mes`
- `dia`
- `ano_mes`
- `dia_semana`
- `trimestre`

---

## 7. Data quality checks

Before generating the Gold layer, the pipeline runs quality checks on the Silver layer.

Implemented validations:

1. Required tables exist.
2. Minimum row count.
3. Key uniqueness:
   - `order_id`
   - `customer_id`
   - `product_id`
4. Negative value validation for `payment_value`.

If any validation fails, the pipeline stops before promoting data to Gold.

---

## 8. Orchestration

The main Airflow DAG is:

~~~text
olist_data_platform_pipeline
~~~

Flow:

~~~text
ingest_bronze -> transform_silver -> quality_checks -> transform_gold
~~~

File:

~~~text
dags/olist_pipeline_dag.py
~~~

The DAG can be manually triggered through the Airflow UI.

---

## 9. Dashboard

Dashboard created in Apache Superset:

~~~text
Olist - Business Indicators
~~~

In the local implementation, the dashboard name may appear as:

~~~text
Olist - Indicadores de Negócio
~~~

Indicators:

1. Monthly revenue.
2. Monthly average ticket.
3. Top 10 categories by revenue.
4. Average delivery time by state.
5. Percentage of delayed orders.
6. Review score distribution.

Views used:

- `vw_receita_mensal`
- `vw_top_categorias`
- `vw_entrega_por_estado`
- `vw_pedidos_atrasados`
- `vw_reviews`

---

## 10. How to run

### Requirements

- Docker Desktop.
- WSL2.
- Ubuntu on WSL.
- Olist dataset downloaded from Kaggle.

### Place CSV files

CSV files must be placed in:

~~~text
data/raw/olist/
~~~

Expected example:

~~~text
olist_customers_dataset.csv
olist_geolocation_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_orders_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
olist_product_category_name_translation.csv
~~~

### Start the environment

~~~bash
docker compose up -d
~~~

### Initialize Airflow, if needed

~~~bash
docker compose run --rm airflow-init
~~~

### Access URLs

Airflow:

~~~text
http://localhost:8080
~~~

User: `admin`  
Password: `admin`

MinIO:

~~~text
http://localhost:9001
~~~

User: `minio`  
Password: `minio123`

Superset:

~~~text
http://localhost:8088
~~~

User: `admin`  
Password: `admin`

---

## 11. Manual pipeline execution

~~~bash
docker compose exec airflow-webserver python /opt/airflow/scripts/01_ingest_bronze.py
~~~

~~~bash
docker compose exec airflow-webserver python /opt/airflow/scripts/02_transform_silver.py
~~~

~~~bash
docker compose exec airflow-webserver python /opt/airflow/scripts/04_quality_checks.py
~~~

~~~bash
docker compose exec airflow-webserver python /opt/airflow/scripts/03_transform_gold.py
~~~

~~~bash
docker compose exec airflow-webserver python /opt/airflow/scripts/05_create_duckdb_views.py
~~~

---

## 12. Idempotency

The pipeline was designed to be re-runnable:

- Bronze keeps timestamped snapshots.
- Silver overwrites the cleaned version.
- Gold overwrites the final tables.
- `fato_pedidos` removes duplicates by `order_id`.
- Re-running the pipeline does not duplicate Gold records.

---

## 13. Decisions and trade-offs

### Local Parquet

The solution uses local Parquet files to simplify execution and ensure reproducibility.

### MinIO

MinIO is included as local object storage, keeping the architecture ready for future evolution.

### DuckDB

DuckDB was chosen as the local query engine due to its operational simplicity and strong performance when reading Parquet files. The challenge accepts DuckDB as an alternative to PySpark for transformations, so it was selected to keep the solution lightweight and reproducible locally.

### Iceberg

The challenge asks for Iceberg/Parquet over MinIO/S3. In this version, the delivery uses Parquet organized into layers and DuckDB for querying. The natural evolution would be to materialize the tables as Apache Iceberg tables over MinIO.

### Trino or Dremio

Trino and Dremio were considered as next steps. To keep the delivery focused and functional, DuckDB was used.

---

## 14. Known limitations

This version prioritizes a functional, reproducible, and simple-to-run end-to-end pipeline.

The current implementation materializes Bronze, Silver, and Gold layers as local Parquet files and uses DuckDB as the query engine for analytical views and Apache Superset consumption.

MinIO is included in `docker-compose.yml` as local object storage and as a foundation for future architectural evolution, but it is not used as the main storage for analytical tables in this version.

The challenge asks for Apache Iceberg/Parquet over MinIO or S3. This part was treated as an architectural evolution. For a production-ready version, the natural next steps would be:

1. Materialize Bronze, Silver, and Gold layers as Apache Iceberg tables over MinIO.
2. Add an Iceberg catalog, such as REST Catalog, Hive Metastore, Nessie, or JDBC Catalog.
3. Use Trino, Dremio, or Spark as the main engine for reading and writing Iceberg tables.
4. Connect Superset to Trino or Dremio instead of consuming a local DuckDB file directly.
5. Implement incremental writes with snapshot control, schema evolution, and proper partitioning.

This decision was made to avoid excessive local environment complexity and to ensure that the full flow, from ingestion to dashboard, remained functional within the available time.

---

## 15. What I would do with more time

Future improvements:

1. Materialize Apache Iceberg tables over MinIO.
2. Add Trino or Dremio as the main query engine.
3. Implement tests with Great Expectations or Pandera.
4. Add partitioning by order date.
5. Implement incremental upserts.
6. Create CI/CD with DAG validation.
7. Externalize configurations through environment variables.
8. Add structured logging.
9. Create pipeline failure monitoring.
10. Add semantic versioning for data lake layers.

---

## 16. Project structure

~~~text
olist-data-platform/
├── config/
├── dags/
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── logs/
├── plugins/
├── scripts/
├── sql/
├── docker-compose.yml
├── requirements.txt
└── README.md
~~~

---

# 🇧🇷 Versão em Português

## 1. Visão geral

Projeto desenvolvido como teste prático para a vaga de Engenheiro(a) de Dados - nível Pleno.

A solução implementa uma plataforma analítica end-to-end usando dados públicos da Olist, enriquecidos com uma API pública de feriados nacionais. O pipeline organiza os dados em camadas Bronze, Silver e Gold, aplica checagens de qualidade, gera um modelo dimensional e disponibiliza indicadores de negócio em um dashboard no Apache Superset.

---

## 2. Objetivo

Construir uma pipeline analítica local e reprodutível com:

- Ingestão de dados CSV da Olist.
- Ingestão de uma fonte adicional via API pública.
- Organização em camadas Bronze, Silver e Gold.
- Transformações com Python/Pandas e DuckDB.
- Orquestração com Apache Airflow.
- Armazenamento em Parquet.
- Consulta analítica com DuckDB.
- Visualização no Apache Superset.
- Execução local via Docker Compose.

---

## 3. Arquitetura

Fluxo geral:

~~~text
Olist CSVs + BrasilAPI
        |
        v
Bronze
        |
        v
Silver
        |
        v
Quality Checks
        |
        v
Gold - Modelo Dimensional
        |
        v
DuckDB Views
        |
        v
Apache Superset
~~~

Componentes principais:

| Componente | Função |
|---|---|
| Docker Compose | Sobe o ambiente local |
| Airflow | Orquestra a pipeline |
| Postgres | Banco de metadados do Airflow |
| MinIO | Object storage local disponível no ambiente |
| Python/Pandas | Ingestão, limpeza e padronização dos dados |
| DuckDB | Transformações analíticas, views e consulta sobre Parquet |
| Parquet | Formato analítico das camadas |
| Superset | Dashboard de indicadores |

---

## 4. Fontes de dados

### Dataset principal

Foi utilizado o dataset público Brazilian E-Commerce Public Dataset by Olist, disponível no Kaggle.

Arquivos utilizados:

- `olist_orders_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_products_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_product_category_name_translation.csv`

### Fonte adicional via API

Para atender ao requisito de múltiplas fontes, foi usada a API pública da BrasilAPI:

~~~text
https://brasilapi.com.br/api/feriados/v1/2018
~~~

Os dados de feriados foram ingeridos na Bronze e promovidos para Silver como `dim_feriados`.

---

## 5. Camadas de dados

### Bronze

Local:

~~~text
data/bronze/
~~~

Características:

- Armazena snapshots brutos em Parquet.
- Mantém metadados de origem.
- Não aplica regras de negócio.
- Preserva histórico de ingestão por timestamp.

### Silver

Local:

~~~text
data/silver/
~~~

Transformações:

- Normalização de nomes de colunas.
- Conversão de datas.
- Remoção de duplicados.
- Padronização de textos.
- Tratamento inicial de inconsistências.

### Gold

Local:

~~~text
data/gold/
~~~

Tabelas geradas:

- `fato_pedidos`
- `dim_cliente`
- `dim_produto`
- `dim_tempo`

Também é gerado o arquivo:

~~~text
data/gold/olist_analytics.duckdb
~~~

Esse arquivo contém views usadas pelo Superset.

---

## 6. Modelo dimensional

### `fato_pedidos`

Granularidade: um registro por pedido.

| Campo | Descrição |
|---|---|
| `order_id` | Identificador do pedido |
| `customer_id` | Chave do cliente |
| `product_id` | Produto principal do pedido |
| `seller_id` | Vendedor principal |
| `data_pedido` | Data da compra |
| `order_status` | Status do pedido |
| `qtd_itens` | Quantidade de itens |
| `valor_produtos` | Soma dos produtos |
| `valor_frete` | Soma do frete |
| `payment_value` | Valor pago |
| `review_score` | Nota média do review |
| `entregue_com_atraso` | Indica se houve atraso |
| `tempo_entrega_dias` | Tempo de entrega em dias |

### `dim_cliente`

Granularidade: um registro por `customer_id`.

Campos principais:

- `customer_id`
- `customer_unique_id`
- `customer_zip_code_prefix`
- `customer_city`
- `customer_state`

### `dim_produto`

Granularidade: um registro por `product_id`.

Campos principais:

- `product_id`
- `product_category_name`
- `product_category_name_english`
- `product_weight_g`
- `product_length_cm`
- `product_height_cm`
- `product_width_cm`

### `dim_tempo`

Granularidade: um registro por data de pedido.

Campos principais:

- `data`
- `ano`
- `mes`
- `dia`
- `ano_mes`
- `dia_semana`
- `trimestre`

---

## 7. Checagens de qualidade

Antes da geração da Gold, o pipeline executa checagens de qualidade na Silver.

Validações implementadas:

1. Existência das tabelas obrigatórias.
2. Contagem mínima de registros.
3. Unicidade de chaves:
   - `order_id`
   - `customer_id`
   - `product_id`
4. Validação de valores negativos em `payment_value`.

Se alguma validação falhar, a pipeline é interrompida antes da promoção para Gold.

---

## 8. Orquestração

A DAG principal do Airflow é:

~~~text
olist_data_platform_pipeline
~~~

Fluxo:

~~~text
ingest_bronze -> transform_silver -> quality_checks -> transform_gold
~~~

Arquivo:

~~~text
dags/olist_pipeline_dag.py
~~~

A DAG pode ser executada manualmente pela interface do Airflow.

---

## 9. Dashboard

Dashboard criado no Apache Superset:

~~~text
Olist - Indicadores de Negócio
~~~

Indicadores:

1. Receita mensal.
2. Ticket médio mensal.
3. Top 10 categorias por receita.
4. Tempo médio de entrega por estado.
5. Percentual de pedidos atrasados.
6. Distribuição das notas de review.

Views utilizadas:

- `vw_receita_mensal`
- `vw_top_categorias`
- `vw_entrega_por_estado`
- `vw_pedidos_atrasados`
- `vw_reviews`

---

## 10. Como executar

### Pré-requisitos

- Docker Desktop.
- WSL2.
- Ubuntu no WSL.
- Dataset da Olist baixado do Kaggle.

### Colocar os CSVs

Os CSVs devem ficar em:

~~~text
data/raw/olist/
~~~

Exemplo esperado:

~~~text
olist_customers_dataset.csv
olist_geolocation_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_orders_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
olist_product_category_name_translation.csv
~~~

### Subir ambiente

~~~bash
docker compose up -d
~~~

### Inicializar Airflow, se necessário

~~~bash
docker compose run --rm airflow-init
~~~

### Acessos

Airflow:

~~~text
http://localhost:8080
~~~

Usuário: `admin`  
Senha: `admin`

MinIO:

~~~text
http://localhost:9001
~~~

Usuário: `minio`  
Senha: `minio123`

Superset:

~~~text
http://localhost:8088
~~~

Usuário: `admin`  
Senha: `admin`

---

## 11. Execução manual da pipeline

~~~bash
docker compose exec airflow-webserver python /opt/airflow/scripts/01_ingest_bronze.py
~~~

~~~bash
docker compose exec airflow-webserver python /opt/airflow/scripts/02_transform_silver.py
~~~

~~~bash
docker compose exec airflow-webserver python /opt/airflow/scripts/04_quality_checks.py
~~~

~~~bash
docker compose exec airflow-webserver python /opt/airflow/scripts/03_transform_gold.py
~~~

~~~bash
docker compose exec airflow-webserver python /opt/airflow/scripts/05_create_duckdb_views.py
~~~

---

## 12. Idempotência

A pipeline foi construída para ser reprocessável:

- Bronze mantém snapshots por timestamp.
- Silver sobrescreve a versão tratada.
- Gold sobrescreve as tabelas finais.
- `fato_pedidos` remove duplicidade por `order_id`.
- Reexecutar a pipeline não duplica registros na Gold.

---

## 13. Decisões e trade-offs

### Parquet local

A solução usa arquivos Parquet locais para simplificar a execução e garantir reprodutibilidade.

### MinIO

O MinIO foi incluído no ambiente como object storage local, deixando a arquitetura preparada para evolução.

### DuckDB

DuckDB foi usado como query engine local pela simplicidade operacional e boa performance para leitura de Parquet. O enunciado aceita DuckDB como alternativa ao PySpark para transformação, por isso ele foi escolhido para manter a solução mais leve e reprodutível localmente.

### Iceberg

O enunciado solicita Iceberg/Parquet sobre MinIO/S3. Nesta versão, a entrega usa Parquet organizado em camadas e DuckDB para consulta. A evolução natural seria materializar as tabelas como Apache Iceberg sobre MinIO.

### Trino ou Dremio

Trino e Dremio foram considerados como próximos passos. Para manter a entrega objetiva e funcional, foi usado DuckDB.

---

## 14. Limitações conhecidas

A versão entregue prioriza uma pipeline end-to-end funcional, reprodutível e simples de executar localmente.

A implementação atual materializa as camadas Bronze, Silver e Gold em arquivos Parquet locais e utiliza DuckDB como query engine para criação de views analíticas e consumo pelo Apache Superset.

O MinIO foi incluído no `docker-compose.yml` como object storage local e base para evolução da arquitetura, mas nesta versão ele ainda não é usado como storage principal das tabelas analíticas.

O enunciado solicita Apache Iceberg/Parquet sobre MinIO ou S3. Essa parte foi tratada como evolução arquitetural. Para uma versão produtiva ou mais aderente à stack final, a evolução natural seria:

1. Materializar as camadas Bronze, Silver e Gold como tabelas Apache Iceberg sobre MinIO.
2. Adicionar um catálogo Iceberg, como REST Catalog, Hive Metastore, Nessie ou JDBC Catalog.
3. Usar Trino, Dremio ou Spark como engine principal de leitura e escrita das tabelas Iceberg.
4. Conectar o Superset ao Trino ou Dremio, em vez de consumir diretamente o arquivo DuckDB local.
5. Implementar escrita incremental com controle de snapshots, schema evolution e particionamento adequado.

Essa decisão foi tomada para evitar complexidade excessiva no ambiente local e garantir que o fluxo completo, desde ingestão até dashboard, estivesse funcional dentro do prazo.

---

## 15. O que eu faria com mais tempo

Melhorias futuras:

1. Materializar tabelas Apache Iceberg sobre MinIO.
2. Adicionar Trino ou Dremio como query engine principal.
3. Implementar testes com Great Expectations ou Pandera.
4. Adicionar particionamento por data de pedido.
5. Implementar upsert incremental.
6. Criar CI/CD com validação de DAGs.
7. Externalizar configurações via variáveis de ambiente.
8. Adicionar logs estruturados.
9. Criar monitoramento de falhas.
10. Versionar semanticamente as camadas do data lake.

---

## 16. Estrutura do projeto

~~~text
olist-data-platform/
├── config/
├── dags/
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── logs/
├── plugins/
├── scripts/
├── sql/
├── docker-compose.yml
├── requirements.txt
└── README.md
~~~
