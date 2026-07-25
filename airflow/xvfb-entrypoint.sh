#!/usr/bin/env bash
# Wraps the official Airflow image's own entrypoint (dumb-init -> /entrypoint)
# so scheduler tasks that launch Chromium with headless=False (see
# scrapers/config.py) have a display to render into. Only the scheduler
# service needs this - the webserver never launches a browser.
set -e

# A container restart (e.g. after a crash, under restart: unless-stopped)
# reuses the same filesystem rather than a fresh one, so a lock file from
# the previous Xvfb process would otherwise make every restart fail.
rm -f /tmp/.X99-lock

Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp &
export DISPLAY=:99

exec /usr/bin/dumb-init -- /entrypoint "$@"
