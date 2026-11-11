# IDeal – CSIT314 Group Project

An online platform that matches renovation customers with interior designers (IDs).
Built with Python Flask + SQLite using the **boundary–control–entity (b-c-e)** design.

## Run it locally

You need Python 3.10 or newer.

```bash
pip install -r requirements.txt
python scripts/seed_data.py
python scripts/seed_project_interest.py
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

## CI/CD

The pipeline in `.github/workflows/ci.yml` runs on every push and pull request to `main`:

| Stage | Runs on | What it does |
|---|---|---|
| Test | every push and PR | Runs all unit tests, uploads the test report, checks the test data scripts |
| Build and smoke test | every push and PR | Builds the Docker image, starts it and checks the login page loads |
| Publish image | push to `main` | Pushes the image to GitHub Container Registry as `latest` and the commit SHA |
| Deploy to Render | push to `main` | Triggers a Render deploy (skipped until `RENDER_DEPLOY_HOOK_URL` is set) |

Each stage only runs if the one before it passed.

Run the published image:

```bash
docker run -p 8000:8000 ghcr.io/yamtaro99/csit314:latest
```

To turn on the Render deploy, create a Render Blueprint from this repo (it reads `render.yaml`),
copy the service's deploy hook URL, and add it to GitHub as the repository secret `RENDER_DEPLOY_HOOK_URL`.
The free plan has no persistent disk, so the test data is rebuilt on every start.

## Project layout

```
app/
  boundary/     pages: Flask routes (one file per feature area)
  control/      controllers: one class per use case
  entity/       domain classes that hold data and save/load themselves
  templates/    HTML for the boundaries
  schema.sql    all database tables
scripts/       test data generators
Dockerfile     container image used by CI/CD and Render
tests/          pytest unit tests (one file per use case)
docs/           diagrams and use case descriptions
```
