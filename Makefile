SHELL := /bin/bash

setup:
	python3 -m venv venv
	pip install -r requirements.txt

serve:
	sudo service postgresql start
	uvicorn backend.main:app --reload

clean:
	sudo find . -type f -name "*.pyc" -delete
	sudo find . -type d -name "__pycache__" -delete
	sudo rm -rf venv