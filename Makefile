.PHONY: install judge-run test

install:
	pip install -r requirements.txt
	python -m playwright install chromium

judge-run: install
	uvicorn main:app --host 127.0.0.1 --port 8000
