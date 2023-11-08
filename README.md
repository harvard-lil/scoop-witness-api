# Scoop Witness API 🍨

[![Linting](https://github.com/harvard-lil/scoop-witness-api/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/harvard-lil/scoop-witness-api/actions/workflows/lint.yml) [![Test suite](https://github.com/harvard-lil/scoop-witness-api/actions/workflows/tests.yml/badge.svg)](https://github.com/harvard-lil/scoop-witness-api/actions/workflows/tests.yml)

A simple REST API for witnessing the web using the Scoop web archiving capture engine.

This first iteration is built around: 
- [Flask](https://flask.palletsprojects.com/en/2.3.x/)
- [Custom Flask commands](https://flask.palletsprojects.com/en/2.3.x/cli/#custom-commands)
- [SQLite](https://www.sqlite.org/index.html)

---

## Summary
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [CLI](#cli)
- [API](#api)
- [Deployment](#deployment)
- [Tests and linting](#tests-and-linting)

---

## Getting Started

Note: this application has only been tested on UNIX-like systems.

### 1. Machine-level dependencies
- [Python 3.9+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/en)
- [Poetry](https://python-poetry.org/)

### 2. Project-level dependencies
The following shortcut will:
- Install all Python dependencies using `poetry`
- Install Scoop and related dependencies using `npm`

```bash
bash install.sh
```

### 3. Setting up configuration

Copy `scoop_witness_api/config.example.py` as `scoop_witness_api/config.py` and adjust as needed.

If you would like to use an alternative way of providing configuration, see:
- https://flask.palletsprojects.com/en/2.3.x/config/#configuring-from-data-files
- https://flask.palletsprojects.com/en/2.3.x/config/#configuring-from-environment-variables
... and update `scoop_witness_api/__init__.py` accordingly.


### 4. Setting up the database
The following command creates and initializes the database tables for the application to use. 

```bash
poetry run flask create-tables
```

### 5. Starting the server
The following command starts the development server on port 5000.

```bash
poetry run flask run 
```

### 6. Starting the capture process
The following command starts the capture process.

```bash
poetry run flask start-capture-process
# Capture process runs until interrupted
```

Alternatively, this command can be used to run parallel capture processes:
```bash
poetry run flask start-parallel-capture-processes
```

More details in the [CLI](#CLI) and [API](#API) sections of this document.

[👆 Back to the summary](#summary)

---

## Configuration

The application's settings are defined globally using [Flask's configuration system](https://flask.palletsprojects.com/en/2.3.x/config/).

All available options listed detailed in [config.example.py](https://github.com/harvard-lil/scoop-witness-api/blob/main/scoop_witness_api/config.example.py), which needs to be copied and edited as `config.py`.

[config.example.py](https://github.com/harvard-lil/scoop-witness-api/blob/main/scoop_witness_api/config.py) can be edited in place and used as-is, or replaced with another file / method of storing configuration data that Flask supports. 

Be sure to edit [`__init__.py` accordingly if you choose to use a different method of providing settings to Flask](https://github.com/harvard-lil/scoop-witness-api/blob/main/scoop_witness_api/__init__.py#L9).

With few exceptions -- all related to input/output --, all of the [CLI options available for Scoop](https://github.com/harvard-lil/scoop#using-scoop-on-the-command-line) can be configured and tweaked in [config.example.py](https://github.com/harvard-lil/scoop-witness-api/blob/main/config.example.py).

[👆 Back to the summary](#summary)

---

## CLI

This application was built using [Flask](https://flask.palletsprojects.com/) for both its REST API and CLI components. 

Custom commands were created as a way to operate the application and administer it.  

<details>
    <summary><strong>Listing available commands</strong></summary>

```bash
poetry run flask --help`
# Sub-commands also have a help menu:
poetry run flask create-access-key --help
```
</details>

<details>
    <summary><strong>create-tables</strong></summary>

```bash
poetry run flask create-tables
```

Creates a new SQLite database if needed and populates it with tables. 
</details>

<details>
    <summary><strong>create-access-key</strong></summary>

```bash
poetry run flask create-access-key --label "John Doe"
```

Creates a new API access key. Said access key will only be displayed once, as a result of this command.
</details>

<details>
    <summary><strong>cancel-access-key</strong></summary>

```bash
poetry run flask cancel-access-key --id_access_key 1
```

Makes a given access key inoperable.
</details>

<details>
    <summary><strong>status</strong></summary>

```bash
poetry run flask status
```

Lists access key ids, as well as pending and started captures.
</details>

<details>
    <summary><strong>start-capture-process</strong></summary>

```bash
poetry run flask start-capture-process
```

Starts a capture process. Runs until it is manually interrupted with SIGINT (Ctrl + C). 

This process: 
- Picks a pending capture request from the database, if any
- Marks it as started
- Uses Scoop to complete the capture
- Store results 
- Starts over / waits for a new request to come in

The `--proxy-port` option allows to specify on which port the proxy should run on:

```bash
poetry run flask start-capture-process --proxy-port 9905
```

</details>

<details>
    <summary><strong>start-parallel-capture-processes</strong></summary>

```bash
poetry run flask start-parallel-capture-processes
```

Starts parallel capture processes, the number of which is determined at [application configuration](#configuration) level.
</details>

<details>
    <summary><strong>cleanup</strong></summary>

```bash
poetry run flask cleanup
```

Removes _"expired"_ files from storage. 
Shelf-life is determined by `TEMPORARY_STORAGE_EXPIRATION` at [application configuration](#configuration) level.

This command should ideally be run on a scheduler.
</details>

<details>
    <summary><strong>inspect-capture</strong></summary>

```bash
poetry run flask inspect-capture --id_capture "8130d6fe-4adb-4142-a685-00a64bb6ff29"
```

Returns full details about a given capture as JSON. Can be used by administrators to inspect logs.
</details>

[👆 Back to the summary](#summary)

---

## API

**Note:**
Unless specified otherwise, every capture-related object returned by the API is [generated using `capture_to_dict()`](https://github.com/harvard-lil/scoop-witness-api/blob/main/scoop_witness_api/utils/capture_to_dict.py).


<details>
    <summary><strong>[GET] /</strong></summary>

Simple _"ping"_ route to ensure the API is running.
Returns HTTP 200 and an empty body.
</details>

<details>
    <summary><strong>[POST] /capture</strong></summary>

Creates a capture request.

**Authentication:** Requires a valid access key, passed via the `Access-Key` header.

Accepts JSON body with the following properties:
- `url`: URL to capture (required)
- `callback_url`: URL to be called once capture is complete (optional). This URL will receive a JSON object describing the capture request and its current status.

Returns HTTP 200 and capture info.

The capture request will be rejected if the capture server is over capacity, as defined by the `MAX_PENDING_CAPTURES` setting in `config.py`.

**Sample request:**
```json
{
  "url": "https://lil.law.harvard.edu",
}
```

**Sample response:**
```json
{
  "callback_url": null,
  "created_timestamp": "Wed, 28 Jun 2023 16:30:28 GMT",
  "ended_timestamp": null,
  "follow": "https://scoop-witness-api.host/capture/5234bb37-58a8-4071-a65c-0f7815da5202",
  "id_capture": "5234bb37-58a8-4071-a65c-0f7815da5202",
  "started_timestamp": null,
  "status": "pending",
  "url": "https://lil.law.harvard.edu"
}
```

The `follow` property is a direct link to `[GET] /capture/<id_capture>`, described below.  

</details>

<details>
    <summary><strong>[GET] /capture/&lt;id_capture&gt;</strong></summary>

Returns information about a specific capture.

**Authentication:** Requires a valid access key, passed via the `Access-Key` header. Access is limited to captures initiated using said access key.

**Sample response:**
```json
{
  "artifacts": [
    "https://scoop-witness-api.host/artifact/2eb7145f-dd8e-4354-bf06-6afc6015c446/archive.wacz",
    "https://scoop-witness-api.host/artifact/2eb7145f-dd8e-4354-bf06-6afc6015c446/provenance-summary.html",
    "https://scoop-witness-api.host/artifact/2eb7145f-dd8e-4354-bf06-6afc6015c446/screenshot.png",
    "https://scoop-witness-api.host/artifact/2eb7145f-dd8e-4354-bf06-6afc6015c446/lil.law.harvard.edu.pem",
    "https://scoop-witness-api.host/artifact/2eb7145f-dd8e-4354-bf06-6afc6015c446/analytics.lil.tools.pem"
  ],
  "callback_url": null,
  "created_timestamp": "Wed, 28 Jun 2023 16:30:28 GMT",
  "ended_timestamp": "Wed, 28 Jun 2023 16:30:45 GMT",
  "id_capture": "2eb7145f-dd8e-4354-bf06-6afc6015c446",
  "started_timestamp": "Wed, 28 Jun 2023 16:30:30 GMT",
  "status": "success",
  "temporary_playback_url": "https://replayweb.page/?source=https://scoop-witness-api.host/artifact/2eb7145f-dd8e-4354-bf06-6afc6015c446/archive.wacz",
  "url": "https://lil.law.harvard.edu"
}
```

The entries under `artifacts` are direct links to `[GET] /artifact/<id_capture>/<filename>`.

`temporary_playback_url` allows for checking the resulting WACZ against [replayweb.page](https://replayweb.page).

</details>

<details>
    <summary><strong>[GET] /artifact/&lt;id_capture&gt;/&lt;filename&gt;</strong></summary>

Allows for accessing and downloading artifacts generated as part of the capture process.

This route is not access-controlled.

Files are only stored temporarily ([see `cleanup` CLI command](#cli)).
</details>

[👆 Back to the summary](#summary)

---

## Deployment

Flask applications can be deployed in many different ways, therefore this section will focus mostly on what is specific about this project:
- The Flask application itself should be run using a production-ready WSGI server such as [gunicorn](https://gunicorn.org/), and ideally put [behind a reverse proxy](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04).
- The `start-parallel-capture-processes` command should run continually in a dedicated process.
- The `cleanup` command should be run on a scheduler, for example every 5 minutes.

### Running in headful mode
The default settings assume that [Scoop runs in headful mode](https://github.com/harvard-lil/scoop-witness-api/blob/main/scoop_witness_api/config.py#L88), which [generally yields better results](https://github.com/harvard-lil/scoop#should-i-run-scoop-in-headful-mode). 

Running in headful mode requires that a window system, if none is available:
- You may consider switching to headless mode (`--headless true`)
- Or use `xvfb-run` to provide a simulated X environment to the `start-parallel-capture-processes` command:
```bash
xvfb-run --auto-servernum -- flask start-parallel-capture-processes
```

[👆 Back to the summary](#summary)

---

## Tests and linting

This project uses [pytest](https://docs.pytest.org/en/6.2.x/contents.html). 

The test suite creates a _"throw-away"_ database for the duration of the test session. 

The test suite will also create a temporary storage folder that gets deleted at the end of the test suite.

```bash
# Running tests
poetry run pytest -v 

# Run linter
poetry run flake8

# Run auto formatter
poetry run black scoop_witness_api

# Bump app version
poetry version patch
```

[👆 Back to the summary](#summary)
