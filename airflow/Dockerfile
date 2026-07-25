# Extends the official Airflow image with the Playwright/Chromium stack the
# scrapers need, plus Xvfb so the browsers can run with headless=False
# (config.py:BROWSER_LAUNCH keeps that intentionally, to dodge bot detection
# on sites like Acer's store - see scrapers/config.py's comments) even on a
# machine/server with no real display attached.
ARG AIRFLOW_VERSION=2.10.5
ARG PYTHON_VERSION=3.12
FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}
# ARGs above FROM only apply to the FROM line itself - redeclare to use them
# in the RUN below too.
ARG AIRFLOW_VERSION
ARG PYTHON_VERSION

USER root

# xvfb: virtual display for the non-headless browser launches.
RUN apt-get update \
    && apt-get install -y --no-install-recommends xvfb \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY --chown=airflow:root requirements.txt /tmp/requirements.txt
# --constraint pins everything Airflow itself depends on (sqlalchemy,
# psycopg2, etc.) to the versions that image's own release was tested
# against, so this install can only add packages Airflow doesn't already
# have an opinion on - never silently upgrade one out from under it.
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# Split deliberately: install-deps (apt packages like libnss3/libatk) needs
# root, but the browser download itself must run as the airflow user - the
# container runs as airflow at runtime (docker-compose's `user:`), and a
# browser downloaded under root's home wouldn't be visible to it. Pinning
# PLAYWRIGHT_BROWSERS_PATH keeps this build step and the runtime container
# looking in the same place regardless of how each resolves $HOME.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/airflow/pw-browsers
USER root
RUN python -m playwright install-deps chromium
USER airflow
RUN python -m playwright install chromium

COPY --chown=airflow:root xvfb-entrypoint.sh /opt/airflow/xvfb-entrypoint.sh
USER root
RUN chmod +x /opt/airflow/xvfb-entrypoint.sh
USER airflow

ENV PYTHONPATH=/opt/airflow/project
