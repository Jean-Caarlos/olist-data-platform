# Olist Data Platform

Projeto desenvolvido como teste prático para a vaga de Engenheiro(a) de Dados - nível Pleno.

A solução implementa uma plataforma analítica end-to-end usando dados públicos da Olist, enriquecidos com uma API pública de feriados nacionais. O pipeline organiza os dados em camadas Bronze, Silver e Gold, aplica checagens de qualidade, gera um modelo dimensional e disponibiliza indicadores de negócio em um dashboard no Apache Superset.

---

## 1. Objetivo

Construir uma pipeline analítica local e reprodutível com:

- Ingestão de dados CSV da Olist.
- Ingestão de uma fonte adicional via API pública.
- Organização em camadas Bronze, Silver e Gold.
- Transformações com Python, Pandas e DuckDB.
- Orquestração com Apache Airflow.
- Armazenamento em Parquet.
- Consulta analítica com DuckDB.
- Visualização no Apache Superset.
- Execução local via Docker Compose.

---

## 2. Arquitetura

Fluxo geral:

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

Componentes principais:

| Componente | Função |
|---|---|
| Docker Compose | Sobe o ambiente local |
| Airflow | Orquestra a pipeline |
| Postgres | Banco de metadados do Airflow |
| MinIO | Object storage local disponível no ambiente |
| Python/Pandas | Ingestão e transformação |
| Parquet | Formato analítico das camadas |
| DuckDB | Engine analítica local |
| Superset | Dashboard de indicadores |

---

## 3. Fontes de dados

### Dataset principal

Foi utilizado o dataset público Brazilian E-Commerce Public Dataset by Olist, disponível no Kaggle.

Arquivos utilizados:

- olist_orders_dataset.csv
- olist_customers_dataset.csv
- olist_order_items_dataset.csv
- olist_order_payments_dataset.csv
- olist_products_dataset.csv
- olist_sellers_dataset.csv
- olist_order_reviews_dataset.csv
- olist_geolocation_dataset.csv
- olist_product_category_name_translation.csv

### Fonte adicional via API

Para atender ao requisito de múltiplas fontes, foi usada a API pública da BrasilAPI:

https://brasilapi.com.br/api/feriados/v1/2018

Os dados de feriados foram ingeridos na Bronze e promovidos para Silver como dim_feriados.

---

## 4. Camadas de dados

### Bronze

Local:

data/bronze/

Características:

- Armazena snapshots brutos em Parquet.
- Mantém metadados de origem.
- Não aplica regras de negócio.
- Preserva histórico de ingestão por timestamp.

### Silver

Local:

data/silver/

Transformações:

- Normalização de nomes de colunas.
- Conversão de datas.
- Remoção de duplicados.
- Padronização de textos.
- Tratamento inicial de inconsistências.

### Gold

Local:

data/gold/

Tabelas geradas:

- fato_pedidos
- dim_cliente
- dim_produto
- dim_tempo

Também é gerado o arquivo:

data/gold/olist_analytics.duckdb

Esse arquivo contém views usadas pelo Superset.

---

## 5. Modelo dimensional

### fato_pedidos

Granularidade: um registro por pedido.

Principais campos:

| Campo | Descrição |
|---|---|
| order_id | Identificador do pedido |
| customer_id | Chave do cliente |
| product_id | Produto principal do pedido |
| seller_id | Vendedor principal |
| data_pedido | Data da compra |
| order_status | Status do pedido |
| qtd_itens | Quantidade de itens |
| valor_produtos | Soma dos produtos |
| valor_frete | Soma do frete |
| payment_value | Valor pago |
| review_score | Nota média do review |
| entregue_com_atraso | Indica se houve atraso |
| tempo_entrega_dias | Tempo de entrega em dias |

### dim_cliente

Granularidade: um registro por customer_id.

Campos principais:

- customer_id
- customer_unique_id
- customer_zip_code_prefix
- customer_city
- customer_state

### dim_produto

Granularidade: um registro por product_id.

Campos principais:

- product_id
- product_category_name
- product_category_name_english
- product_weight_g
- product_length_cm
- product_height_cm
- product_width_cm

### dim_tempo

Granularidade: um registro por data de pedido.

Campos principais:

- data
- ano
- mes
- dia
- ano_mes
- dia_semana
- trimestre

---

## 6. Checagens de qualidade

Antes da geração da Gold, o pipeline executa checagens de qualidade na Silver.

Validações implementadas:

1. Existência das tabelas obrigatórias.
2. Contagem mínima de registros.
3. Unicidade de chaves:
   - order_id
   - customer_id
   - product_id
4. Validação de valores negativos em payment_value.

Se alguma validação falhar, a pipeline é interrompida antes da promoção para Gold.

---

## 7. Orquestração

A DAG principal do Airflow é:

olist_data_platform_pipeline

Fluxo:

ingest_bronze -> transform_silver -> quality_checks -> transform_gold

Arquivo:

dags/olist_pipeline_dag.py

A DAG pode ser executada manualmente pela interface do Airflow.

---

## 8. Dashboard

Dashboard criado no Apache Superset:

Olist - Indicadores de Negócio

Indicadores:

1. Receita mensal.
2. Ticket médio mensal.
3. Top 10 categorias por receita.
4. Tempo médio de entrega por estado.
5. Percentual de pedidos atrasados.
6. Distribuição das notas de review.

Views utilizadas:

- vw_receita_mensal
- vw_top_categorias
- vw_entrega_por_estado
- vw_pedidos_atrasados
- vw_reviews

---

## 9. Como executar

### Pré-requisitos

- Docker Desktop
- WSL2
- Ubuntu no WSL
- Dataset da Olist baixado do Kaggle

### Colocar os CSVs

Os CSVs devem ficar em:

data/raw/olist/

Exemplo esperado:

- olist_customers_dataset.csv
- olist_geolocation_dataset.csv
- olist_order_items_dataset.csv
- olist_order_payments_dataset.csv
- olist_order_reviews_dataset.csv
- olist_orders_dataset.csv
- olist_products_dataset.csv
- olist_sellers_dataset.csv
- olist_product_category_name_translation.csv

### Subir ambiente

docker compose up -d

### Inicializar Airflow, se necessário

docker compose run --rm airflow-init

### Acessos

Airflow:

http://localhost:8080

Usuário: admin  
Senha: admin

MinIO:

http://localhost:9001

Usuário: minio  
Senha: minio123

Superset:

http://localhost:8088

Usuário: admin  
Senha: admin

---

## 10. Execução manual da pipeline

Também é possível rodar as etapas manualmente:

docker compose exec airflow-webserver python /opt/airflow/scripts/01_ingest_bronze.py

docker compose exec airflow-webserver python /opt/airflow/scripts/02_transform_silver.py

docker compose exec airflow-webserver python /opt/airflow/scripts/04_quality_checks.py

docker compose exec airflow-webserver python /opt/airflow/scripts/03_transform_gold.py

docker compose exec airflow-webserver python /opt/airflow/scripts/05_create_duckdb_views.py

---

## 11. Idempotência

A pipeline foi construída para ser reprocessável:

- Bronze mantém snapshots por timestamp.
- Silver sobrescreve a versão tratada.
- Gold sobrescreve as tabelas finais.
- fato_pedidos remove duplicidade por order_id.
- Reexecutar a pipeline não duplica registros na Gold.

---

## 12. Decisões e trade-offs

### Parquet local

A solução usa arquivos Parquet locais para simplificar a execução e garantir reprodutibilidade.

### MinIO

O MinIO foi incluído no ambiente como object storage local, deixando a arquitetura preparada para evolução.

### DuckDB

DuckDB foi usado como query engine local pela simplicidade operacional e boa performance para leitura de Parquet.

### Iceberg

O enunciado solicita Iceberg/Parquet sobre MinIO/S3. Nesta versão, a entrega usa Parquet organizado em camadas e DuckDB para consulta. A evolução natural seria materializar as tabelas como Apache Iceberg sobre MinIO.

### Trino ou Dremio

Trino e Dremio foram considerados como próximos passos. Para manter a entrega objetiva e funcional, foi usado DuckDB.

---

## 13. O que eu faria com mais tempo

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

## 14. Estrutura do projeto

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

---

## 15. Considerações finais

A solução prioriza clareza, reprodutibilidade e funcionamento end-to-end. O pipeline cobre ingestão, transformação, qualidade, modelagem dimensional e visualização, permitindo demonstrar os principais conceitos esperados em uma plataforma analítica local.
