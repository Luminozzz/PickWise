# Airflow

Orchestrates the scraping pipeline (`backend/database/seed.py` + `scrapers/`)
that used to run via `run_price_update.ps1` + Windows Task Scheduler. Runs
under Docker so the same setup moves to a server unchanged later.

## One-time setup

1. Install Docker Desktop (needs a restart + WSL2 backend on Windows):
   ```
   winget install Docker.DockerDesktop
   ```
   Then launch Docker Desktop once and let it finish its own first-run setup.

2. Copy the env template and adjust the admin login if you want:
   ```
   cp airflow/.env.example airflow/.env
   ```
   No DB credentials go here - `backend/.env` (already present, gitignored)
   is bind-mounted into the containers and read by `backend/database/models.py`
   exactly like it is when you run the pipeline natively.

## Running it

From `airflow/`:

```
docker compose build      # first time, and after editing requirements.txt/Dockerfile
docker compose up -d
```

Airflow UI: http://localhost:8080 (login from `.env`, default admin/admin).

Both DAGs are created paused (`AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION`) -
unpause `pickwise_price_updates` in the UI once you've watched it succeed at
least once manually.

- `pickwise_price_updates` - daily (`0 20 * * *` UTC by default, edit the
  `schedule` in the DAG file to taste), runs Amazon/Shopee/official-store
  price scrapers in parallel. 1:1 replacement for the old scheduled task.
- `pickwise_catalog_sync` - manual trigger only. Re-scrapes product specs
  across brands (`seed_all`) then refreshes Razer colour variants
  (`add_mouse_skins`). Run this from the UI/CLI when onboarding new products.

Stop everything with `docker compose down` (add `-v` to also wipe Airflow's
own metadata DB - never touches the app's DigitalOcean Postgres).

## Notes / gotchas

- The scrapers intentionally launch Chromium with `headless=False` (see
  `scrapers/config.py`) to evade bot detection. The scheduler container runs
  Xvfb (a virtual display) to give it somewhere to render - see
  `xvfb-entrypoint.sh`. The webserver container doesn't need this.
- `.playwright_profile*/` under `scrapers/` are bind-mounted through from the
  host, so persistent browser profiles/cookies survive container restarts
  the same way they do when scrapers run natively.
- Moving this to a server: copy the `airflow/` folder (and the repo it sits
  in) over, put a real `backend/.env` there, `docker compose up -d`. Nothing
  in `docker-compose.yaml` is Windows-specific.
- If you add a package to `requirements.txt` and the build fails with
  `ResolutionImpossible` / "The user requested (constraint) X==...": Airflow's
  own constraints file (see the Dockerfile's `--constraint` flag) already
  pins a version of that package for something Airflow itself depends on.
  Don't pin your own version for it in `requirements.txt` - leave it
  unversioned and let the constraint win (this bit us with sqlalchemy,
  beautifulsoup4, and requests-file while building this out).
