from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "owner": "jean",
    "retries": 1,
}


with DAG(
    dag_id="olist_data_platform_pipeline",
    description="Pipeline Olist: bronze -> silver -> quality checks -> gold",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["olist", "data-engineering", "bronze-silver-gold"],
) as dag:

    ingest_bronze = BashOperator(
        task_id="ingest_bronze",
        bash_command="python /opt/airflow/scripts/01_ingest_bronze.py",
    )

    transform_silver = BashOperator(
        task_id="transform_silver",
        bash_command="python /opt/airflow/scripts/02_transform_silver.py",
    )

    quality_checks = BashOperator(
        task_id="quality_checks",
        bash_command="python /opt/airflow/scripts/04_quality_checks.py",
    )

    transform_gold = BashOperator(
        task_id="transform_gold",
        bash_command="python /opt/airflow/scripts/03_transform_gold.py",
    )

    ingest_bronze >> transform_silver >> quality_checks >> transform_gold
