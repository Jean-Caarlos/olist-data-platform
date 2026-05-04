from pathlib import Path

PROJECT_ROOT = Path("/opt/airflow")

DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"

MINIO_ENDPOINT = "http://minio:9000"
MINIO_BUCKET = "datalake"
MINIO_ACCESS_KEY = "minio"
MINIO_SECRET_KEY = "minio123"
