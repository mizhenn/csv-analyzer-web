.PHONY: venv install run docker-build docker-run clean

venv:
	python -m venv venv

install:
	. venv/bin/activate && pip install -r requirements.txt

run:
	python app.py

clean:
	rm -rf venv __pycache__ *.pyc .pytest_cache

docker-build:
	docker build -t csv-analyzer-web .

docker-run:
	docker run --rm -p 5000:5000 csv-analyzer-web
