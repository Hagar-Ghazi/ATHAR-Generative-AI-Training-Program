# Week 1 Lab: Working with a Public REST API Using Python

A short Python program that calls NASA's **NeoWs (Near Earth Object Web Service)** REST API.
It gets the asteroids passing near Earth over the last 7 days, parses the JSON response
into Python objects, and prints a formatted summary.

## How the requirements are covered

| Requirement | Where |
|---|---|
| API integration | `NeoReport.fetch()` calls `https://api.nasa.gov/neo/rest/v1/feed` with `requests` |
| JSON parsing | `response.json()`, then `Asteroid.from_json()` reads the fields it needs |
| Class implementation | `Asteroid` (a dataclass for one object) and `NeoReport` (fetches the data and provides sorted/filtered views) |
| Formatted output | `NeoReport.print_summary()`: totals, a per-day chart, a table of the closest approaches, and a list of hazardous objects |
| Virtual environment | `.venv/` (see setup below) |
| Environment variables | `NASA_API_KEY` is kept in `.env` and loaded with `python-dotenv` |

## Project files

```
neo_tracker.py     # source code
requirements.txt   # dependencies
.env               # your API key (local only, never commit)
.env.example       # template for .env
.gitignore         # excludes .env and .venv
```

## Setup and run (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then put your key in .env
python neo_tracker.py
```

On macOS/Linux, activate with `source .venv/bin/activate`.

## API key

`.env` is not in this repository. Create it from `.env.example`. You can set it to NASA's public
`NASA_API_KEY=DEMO_KEY`, which works but is limited to about 30 requests per hour, or get a free
personal key at <https://api.nasa.gov>:

```
NASA_API_KEY=your_key_here
```

`.env` is listed in `.gitignore`, so the key is never uploaded. Share `.env.example` instead.
