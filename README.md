# csv-analyzer-web

A modern, production-quality Flask web app to upload CSV files and get comprehensive analysis with an intuitive interface.

## Features

- **File Upload**: Configurable size limit (default 10 MB), in-memory processing (no persistence)
- **Smart Parsing**: Auto-detect delimiter, UTF-8 decode with Latin-1 fallback
- **Comprehensive Analysis**:
  - Dataset dimensions (rows, columns)
  - Column data types
  - Missing values analysis (auto-collapsed when none missing)
  - Duplicate row detection with preview
  - Numeric summary with formatted numbers (commas, 2 decimals)
  - First 10 rows preview
  - Memory usage statistics
- **Modern UI**:
  - Clean Bootstrap interface
  - Sticky table headers with scrolling
  - Responsive design
  - Primary action buttons
- **API**: Health endpoint `/health` returns `{"status": "ok"}`

## Requirements

- Python 3.10+
- pip

## Setup

```bash
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows (PowerShell)
# .\\venv\\Scripts\\Activate.ps1

pip install -r requirements.txt
```

## Run (local)

```bash
python app.py
# or
flask --app app run
```

Open http://127.0.0.1:5000 and upload any CSV file to test the analyzer.

## Configure max upload size

The default upload limit is 10 MB. You can raise or lower this without code changes via an environment variable:

- Set MAX_CONTENT_LENGTH_MB (preferred) or UPLOAD_MAX_MB to the desired size in megabytes.
- The app reads this at startup and updates Flask's MAX_CONTENT_LENGTH accordingly.
- The UI displays the configured limit on the upload page.

Examples:

```bash
# 50 MB limit for local run
export MAX_CONTENT_LENGTH_MB=50
python app.py

# Using Flask runner
export MAX_CONTENT_LENGTH_MB=100
flask --app app run

# Docker: pass an environment variable
docker run --rm -e MAX_CONTENT_LENGTH_MB=200 -p 5000:5000 csv-analyzer-web
```

If you change the environment variable, restart the app so the new limit takes effect.

## Docker (optional)

Build:

```bash
docker build -t csv-analyzer-web .
```

Run:

```bash
docker run --rm -p 5000:5000 csv-analyzer-web
```

Open http://127.0.0.1:5000.

## Troubleshooting

- Encoding issues: the app tries UTF-8 first, then Latin-1. If parsing still fails, save your CSV with UTF-8 encoding and retry.
- Large files: uploads are limited to 10 MB. Reduce the file or sample a subset.
- Weird delimiters: common delimiters (`, ; \\t | :`) are sniffed for display; pandas auto-detection handles most cases.

## CLI utility

You can also analyze a CSV from disk using the command-line interface:

```bash
python analyze_csv.py path/to/your/file.csv
```

This outputs similar statistics to the web UI in a text format.

## Project Structure

```
csv-analyzer-web/
├── app.py                 # Main Flask application
├── analyze_csv.py         # CLI utility for CSV analysis
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── Makefile              # Build automation
├── static/
│   └── style.css         # Custom CSS styles
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Upload form
    └── results.html      # Analysis results
```

## License

MIT. See `LICENSE`.
