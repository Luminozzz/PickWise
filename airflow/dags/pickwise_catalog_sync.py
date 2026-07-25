"""Catalog sync: pull in new/changed product specs, then refresh Razer
colour variants. Not on the Windows Task Scheduler today (that only ran
add_new_product_price) so this stays schedule=None - trigger manually from
the Airflow UI/CLI when onboarding new products, or set a schedule once
you're happy with the cadence.

add_mouse_skins queries Mouse rows already in the DB (see seed.py), so it
must run after seed_all, not in parallel with it.
"""
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "pickwise",
    "retries": 1,
}

with DAG(
    dag_id="pickwise_catalog_sync",
    description="Re-scrape product specs across all brands, then refresh Razer skins",
    default_args=default_args,
    schedule="0 0 1 * *", # day 1 of every month
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["pickwise", "scraping", "catalog"],
) as dag:

    def _seed_all():
        from backend.database.seed import seed_all
        seed_all()

    def _add_mouse_skins():
        from backend.database.seed import add_mouse_skins
        add_mouse_skins()

    seed_all_task = PythonOperator(
        task_id="seed_all",
        python_callable=_seed_all,
    )

    add_mouse_skins_task = PythonOperator(
        task_id="add_mouse_skins",
        python_callable=_add_mouse_skins,
    )

    seed_all_task >> add_mouse_skins_task
