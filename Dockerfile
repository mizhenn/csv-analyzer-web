FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app
COPY . /app

# Create non-root user
RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Use gunicorn with app factory
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:create_app()"]
