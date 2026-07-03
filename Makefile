.PHONY: install test lint data-fetch simulate report pdf clean

install:
	uv sync --all-extras

test:
	uv run pytest tests/ -v --cov=ukethnicproj --cov-report=term-missing

lint:
	uv run ruff check src tests

data-discover:
	uv run python -m ukethnicproj data discover

data-fetch:
	uv run python -m ukethnicproj data fetch

data-validate:
	uv run python -m ukethnicproj data validate

build-base:
	uv run python -m ukethnicproj build-base-population

simulate:
	uv run python -m ukethnicproj simulate --scenario scenarios/illustrative_demonstration.yml

report:
	uv run python -m ukethnicproj report

pdf:
	cd docs && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex

clean:
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
