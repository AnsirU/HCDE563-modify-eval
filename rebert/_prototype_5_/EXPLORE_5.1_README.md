# Prototype 5 — Exploration README

## Exercise Attempted

Explore 5.1 on Prototype 5 (`rebert/_prototype_5_/recommender_5.0.py` + Flask app `rebert/_prototype_5_/web/wsgi`).

Changed how each movie card presents its opening date: instead of the raw TMDB `YYYY-MM-DD` string, the card shows a friendlier label based on whether the release is in the past, today, or the future (for example, `Opened on January 12, 2025` or `Opening in 3 days!`).

## Modifications

- **`utilities.py`**: Added `format_release_date()` to parse a `YYYY-MM-DD` release date, compare it to today (or an optional reference date), and return:
  - Past: `Opened on {Month} {day}, {year}`
  - Today: `Opening today!`
  - Future (1 day): `Opening in 1 day!`
  - Future (2+ days): `Opening in {n} days!`
  Empty or invalid strings are returned unchanged so the UI does not break.
- **`serve_main_page.py`**: In `compose_poster_item()`, set `poster_item['release']` using `format_release_date(info['release_date'])` instead of passing through the raw date. The template (`mainpage.html`) still renders `{{movie.release}}`; only the server-side value changed.

**Files modified:** `rebert/_prototype_5_/web/utilities.py`, `rebert/_prototype_5_/web/serve_main_page.py`

## GenAI Usage

I used Cursor / GenAI assistance to locate where movie-card release dates are set in Prototype 5, implement `format_release_date()` and wire it into `compose_poster_item()`, and to draft run commands for local testing. I verified the formatter with a small Python check (past / future / today cases) and by running the server and confirming card text on the main page.

## Data

No new datasets were added. Release dates still come from existing TMDB metadata in the daily movie data file (`web/tmp/rebert-p5.0_data_YYYYMMDD.json`); only the display string on highlight cards was changed.

## How to Run

Activate your venv if you use one, then from the prototype directory (Flask’s `--app web/wsgi` is relative to `rebert/_prototype_5_/`):

```bash
source /Users/hza25/Desktop/HCDE563/.venv/bin/activate   # if applicable
cd /Users/hza25/Desktop/HCDE563/rebert/_prototype_5_
export PYTHONPATH="/Users/hza25/Desktop/HCDE563"
python3 recommender_5.0.py
```

(Replace paths if your repo root or venv location differs.) Open **http://127.0.0.1:5000** in a browser. Optional: `python3 recommender_5.0.py -mockup` for the mockup app; `-port <n>` to change the port.

**Note:** On first launch of the day, if no data file exists yet, the server may spend several minutes collecting movie data before the main page is ready; the launcher may not open a browser automatically until data exists.
