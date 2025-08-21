import os
import io
import csv
import logging
from typing import Tuple, Dict, Any

from flask import Flask, render_template, request, flash, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

import pandas as pd
import numpy as np


ALLOWED_EXTENSIONS = {"csv"}
# Configurable max upload size (in MB) via env MAX_CONTENT_LENGTH_MB or UPLOAD_MAX_MB; defaults to 10 MB
MAX_CONTENT_LENGTH_MB = int(os.getenv("MAX_CONTENT_LENGTH_MB", os.getenv("UPLOAD_MAX_MB", "10")))
MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH_MB * 1024 * 1024  # bytes


def create_app(testing: bool = False) -> Flask:
    """
    Flask application factory. Configures app, routes, logging, and error handlers.
    """
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    app.config["TESTING"] = testing

    # Basic logging to stdout
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app.logger.setLevel(logging.INFO)

    @app.after_request
    def after_request(response):
        app.logger.info(
            "%s %s %s %s",
            request.remote_addr,
            request.method,
            request.full_path,
            response.status,
        )
        return response

    def allowed_file(filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    def human_bytes(num: int) -> str:
        """
        Convert a byte count into a human-readable string.
        """
        symbols = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        f = float(num)
        while f >= 1024 and i < len(symbols) - 1:
            f /= 1024.0
            i += 1
        return f"{f:.2f} {symbols[i]}"

    def sniff_delimiter(sample_text: str) -> str:
        """
        Try to sniff the delimiter from a text sample. Default to comma if unknown.
        """
        try:
            dialect = csv.Sniffer().sniff(sample_text, delimiters=[",", ";", "\t", "|", ":"])
            return dialect.delimiter
        except Exception:
            return ","

    def parse_csv_bytes(data_bytes: bytes) -> Tuple[pd.DataFrame, str, str]:
        """
        Decode uploaded bytes, detect delimiter for display, and parse CSV with pandas.

        Returns: (DataFrame, encoding_used, detected_delimiter)
        """
        encoding_used = "utf-8"
        try:
            text = data_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = data_bytes.decode("latin-1")
            encoding_used = "latin-1"

        sample = text[:10000]
        detected_delimiter = sniff_delimiter(sample)

        # Let pandas auto-detect the separator (sep=None) with python engine
        # Note: low_memory is not supported with the 'python' engine in recent pandas versions
        df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
        return df, encoding_used, detected_delimiter

    def compute_stats(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute required statistics and previews for the given DataFrame.
        """
        rows = len(df)
        cols = df.shape[1]

        dtypes_df = pd.DataFrame({
            "Column": df.columns,
            "Dtype": [str(dt) for dt in df.dtypes],
        })

        missing_per_col = df.isna().sum().reset_index()
        missing_per_col.columns = ["Column", "Missing"]

        total_cells = rows * cols
        overall_missing = int(missing_per_col["Missing"].sum())
        overall_missing_pct = (overall_missing / total_cells * 100.0) if total_cells > 0 else 0.0

        duplicates_count = int(df.duplicated().sum())
        dup_preview_df = df[df.duplicated()].head(10)

        numeric_df = df.select_dtypes(include=[np.number])
        has_numeric = not numeric_df.empty
        if has_numeric:
            # Describe numeric columns, show metric names, and format numbers with commas/2-decimals
            numeric_summary_df = df.describe(include=[np.number]).round(2)
            numeric_summary_df = numeric_summary_df.reset_index().rename(columns={"index": "Metric"})
            def _fmt_num(v):
                try:
                    return f"{float(v):,.2f}"
                except Exception:
                    return v
            for col in numeric_summary_df.columns:
                if col != "Metric":
                    numeric_summary_df[col] = numeric_summary_df[col].apply(_fmt_num)
        else:
            numeric_summary_df = pd.DataFrame()

        preview_df = df.head(10)
        mem_usage_bytes = int(df.memory_usage(deep=True).sum())

        return {
            "rows": rows,
            "cols": cols,
            "dtypes_df": dtypes_df,
            "missing_per_col_df": missing_per_col,
            "overall_missing": overall_missing,
            "overall_missing_pct": overall_missing_pct,
            "duplicates_count": duplicates_count,
            "dup_preview_df": dup_preview_df,
            "has_numeric": has_numeric,
            "numeric_summary_df": numeric_summary_df,
            "preview_df": preview_df,
            "mem_usage_bytes": mem_usage_bytes,
        }

    def df_to_html(df: pd.DataFrame) -> str:
        """
        Render a DataFrame to sanitized HTML with Bootstrap table classes.
        """
        return df.to_html(
            classes="table table-striped table-sm table-hover",
            index=False,
            escape=True,
            border=0,
        )

    @app.get("/")
    def index():
        return render_template("index.html", max_size_mb=MAX_CONTENT_LENGTH // (1024 * 1024))

    @app.post("/analyze")
    def analyze():
        if "file" not in request.files:
            flash("No file part in the request.", "danger")
            return render_template("index.html", max_size_mb=MAX_CONTENT_LENGTH // (1024 * 1024)), 400

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file.", "danger")
            return render_template("index.html", max_size_mb=MAX_CONTENT_LENGTH // (1024 * 1024)), 400

        filename = secure_filename(file.filename)
        if not allowed_file(filename):
            flash("Invalid file type. Only .csv files are allowed.", "danger")
            return render_template("index.html", max_size_mb=MAX_CONTENT_LENGTH // (1024 * 1024)), 400

        try:
            data_bytes = file.read()
            if not data_bytes or data_bytes.strip() == b"":
                flash("Uploaded file is empty.", "danger")
                return render_template("index.html", max_size_mb=MAX_CONTENT_LENGTH // (1024 * 1024)), 400

            df, encoding_used, detected_delimiter = parse_csv_bytes(data_bytes)
            stats = compute_stats(df)

            context = {
                "filename": filename,
                "encoding_used": encoding_used,
                "detected_delimiter": detected_delimiter,
                "rows": stats["rows"],
                "cols": stats["cols"],
                "dtypes_html": df_to_html(stats["dtypes_df"]),
                "missing_per_col_html": df_to_html(stats["missing_per_col_df"]),
                "overall_missing": stats["overall_missing"],
                "overall_missing_pct": round(stats["overall_missing_pct"], 2),
                "duplicates_count": stats["duplicates_count"],
                "dup_preview_html": df_to_html(stats["dup_preview_df"]) if stats["duplicates_count"] > 0 else None,
                "has_numeric": stats["has_numeric"],
                "numeric_summary_html": df_to_html(stats["numeric_summary_df"]) if stats["has_numeric"] else None,
                "preview_html": df_to_html(stats["preview_df"]),
                "mem_usage_bytes": stats["mem_usage_bytes"],
                "mem_usage_human": human_bytes(stats["mem_usage_bytes"]),
            }

            flash("Analysis completed successfully.", "success")
            return render_template("results.html", **context), 200

        except pd.errors.EmptyDataError:
            flash("The CSV appears to be empty or has no columns.", "danger")
            return render_template("index.html", max_size_mb=MAX_CONTENT_LENGTH // (1024 * 1024)), 400
        except pd.errors.ParserError as e:
            app.logger.exception("CSV parse error")
            flash(f"Failed to parse CSV: {e}", "danger")
            return render_template("index.html", max_size_mb=MAX_CONTENT_LENGTH // (1024 * 1024)), 400
        except UnicodeDecodeError:
            flash("Failed to decode the file. Try saving as UTF-8 or Latin-1.", "danger")
            return render_template("index.html", max_size_mb=MAX_CONTENT_LENGTH // (1024 * 1024)), 400
        except Exception:
            app.logger.exception("Unexpected error during analysis")
            flash("An unexpected error occurred while analyzing the file.", "danger")
            return render_template("index.html", max_size_mb=MAX_CONTENT_LENGTH // (1024 * 1024)), 500

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(e):
        # Render minimal friendly page via base with content variables
        return render_template("base.html", content_title="Not Found", content_message="The requested resource was not found."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("base.html", content_title="Server Error", content_message="An internal error occurred."), 500

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_file(e):
        max_mb = app.config.get("MAX_CONTENT_LENGTH", MAX_CONTENT_LENGTH) // (1024 * 1024)
        flash(f"File is too large. Maximum allowed size is {max_mb} MB.", "danger")
        return render_template("index.html", max_size_mb=max_mb), 400

    return app


if __name__ == "__main__":
    app = create_app()
    # Production uses gunicorn; this is for local dev
    app.run(host="127.0.0.1", port=5000, debug=False)
