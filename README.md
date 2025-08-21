Thought for 31s
# 📊 CSV Analyzer (Flask)

Upload a CSV and get instant insights — rows, columns, data types, missing values, duplicates, numeric summary, preview, and more.  
Lightweight, local-first, and easy to run.

---

## ✨ Features

- **Fast file upload** — in-memory processing (no files saved), size limit (default **10 MB**)
- **Smart parsing** — auto-detect delimiter; tries **UTF-8**, then falls back to **Latin-1**
- **Comprehensive analysis**
  - Dataset size (rows, columns)
  - Column names & data types
  - Missing values (section auto-collapses when none 🎉)
  - Duplicate rows (with count, optional preview)
  - Numeric summary with formatted numbers (commas, 2 decimals)
  - First 10 rows preview
  - Memory usage statistics
- **Modern UI**
  - Clean, responsive layout
  - Sticky table headers + scrollable tables
  - Clear primary action buttons
- **Health check API** — `GET /health` → `{"status":"ok"}`

---

## 🧰 Requirements

- Python **3.10+**
- `pip`

---

## 🚀 Quick Start (Local)

```bash
python -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows (PowerShell)
# .\venv\Scripts\Activate.ps1

pip install -r requirements.txt
python app.py
# then open http://127.0.0.1:5000


You can also run with Flask’s CLI:

flask --app app run

⚙️ Configure Max Upload Size

Default upload limit: 10 MB. Change it via an environment variable — no code edits needed.

# Example: 50 MB limit (local)
export MAX_CONTENT_LENGTH_MB=50
python app.py

# Or with Flask runner
export MAX_CONTENT_LENGTH_MB=100
flask --app app run

# Docker
docker run --rm -e MAX_CONTENT_LENGTH_MB=200 -p 5000:5000 csv-analyzer-web


After changing the env var, restart the app so the new limit applies.
UPLOAD_MAX_MB is also supported as a fallback name.

🐳 Docker (Optional)

Build

docker build -t csv-analyzer-web .


Run

docker run --rm -p 5000:5000 csv-analyzer-web


Open http://127.0.0.1:5000

🖥 CLI Utility

Analyze a CSV from the terminal (same core stats as the web UI):

python analyze_csv.py path/to/your/file.csv

📁 Project Structure
csv-analyzer-web/
├── app.py                 # Main Flask application
├── analyze_csv.py         # CLI utility for CSV analysis
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
├── Makefile               # (optional) build / run shortcuts
├── static/
│   └── style.css          # Custom CSS styles
└── templates/
    ├── base.html          # Base template
    ├── index.html         # Upload form
    └── results.html       # Analysis results

🧪 Endpoints

GET / — upload form

POST / — analyze uploaded CSV

GET /health — health check ({"status":"ok"})

🆘 Troubleshooting

Encoding errors — the app tries UTF-8, then Latin-1. If it still fails, re-save the CSV as UTF-8 and retry.

File too large — check or raise MAX_CONTENT_LENGTH_MB (see config above).

Odd delimiters — common ones (, ; \t | :) are detected for display; pandas usually auto-detects correctly.

Blank/odd preview — verify the file is a true CSV (not Excel). If it’s .xlsx, export to .csv first.

🔒 Notes

Files are processed in memory and are not persisted to disk.

This app is intended for local analysis / demos, not for storing sensitive data.
