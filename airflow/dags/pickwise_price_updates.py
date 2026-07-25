"""Daily price refresh across every store the scrapers cover.

Mirrors what run_price_update.ps1 + Windows Task Scheduler used to run
(add_new_product_price, i.e. Amazon), plus the Shopee and brand
official-store price scrapers as a second task in the same DAG.

The two tasks run in series, not parallel: every non-Acer scraper (see
scrapers/config.py's BROWSER_LAUNCH) launches Chromium against the same
shared scrapers/.playwright_profile user_data_dir, and Chromium only allows
one instance per profile dir at a time.

Each task imports backend.database.seed lazily, inside the callable, not at
module top-level - that module opens a SQLAlchemy session as a side effect
of import (see seed.py's module-level `session = SessionLocal()`), and an
eager top-level import would mean every DAG-file parse by the scheduler
(every AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL seconds) tries to reach the
DB, rather than only at actual task run time.
"""
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "pickwise",
    "retries": 1,
}

with DAG(
    dag_id="pickwise_price_updates",
    description="Refresh Amazon/official-store prices for all known mice",
    default_args=default_args,
    schedule="0 0 * * 0",  # 20:00 UTC daily - adjust to taste
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["pickwise", "scraping", "prices"],
) as dag:

    def _amazon_price_update():
        from backend.database.seed import add_new_product_price
        add_new_product_price()

    def _official_store_price_update():
        from backend.database.seed import add_official_store_product_price
        add_official_store_product_price()

    amazon_price_update = PythonOperator(
        task_id="amazon_price_update",
        python_callable=_amazon_price_update,
    )

    official_store_price_update = PythonOperator(
        task_id="official_store_price_update",
        python_callable=_official_store_price_update,
    )

    amazon_price_update >> official_store_price_update
