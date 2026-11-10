# IDeal – CSIT314 Group Project

An online platform that matches renovation customers with interior designers (IDs).
Built with Python Flask + SQLite using the **boundary–control–entity (b-c-e)** design.

## Run it locally

You need Python 3.10 or newer.

```bash
pip install -r requirements.txt
python scripts/seed_data.py          # builds the database with ~200 users and ~220 projects
python scripts/seed_project_interest.py # populate database for project interest
python scripts/create_project_report_table.py  # ensures the UC37 report table exists
python -m flask --app app run --debug
```

Open http://localhost:5000 and log in with any seeded account. All of them use the password `Password123!`.

| Role | Example login |
|---|---|
| User Admin | `admin@ideal.test` |
| Platform Manager | `pm1@ideal.test` … `pm5@` |
| Interior Designer | `designer001@ideal.test` … `designer090@` (091–100 are pending approval) |
| Customer | `customer001@ideal.test` … `customer100@` (every 25th is suspended) |

## Run the tests

```bash
python -m pytest -v
```

GitHub Actions runs the same tests on every push and pull request (`.github/workflows/ci.yml`).

## Deployment

Pushes to `main` that pass the tests trigger a deploy to Render.com (`render.yaml`). To set it up:
create a Render web service from this repo, turn off its "Auto-Deploy", and add the service's deploy hook URL
to GitHub as the repository secret `RENDER_DEPLOY_HOOK_URL`. The free plan has no persistent disk, so the
test data is rebuilt on every start.

## Project layout

```
app/
  boundary/     pages: Flask routes (one file per feature area)
  control/      controllers: one class per use case
  entity/       domain classes that hold data and save/load themselves
  templates/    HTML for the boundaries
  schema.sql    all database tables
scripts/seed_data.py   random test data generator
tests/          pytest unit tests (one file per use case)
docs/           diagrams and use case descriptions
```
