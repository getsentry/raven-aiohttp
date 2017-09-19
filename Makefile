develop:
	@echo "--> Installing dependencies"
	pip install -e .
	pip install "file://`pwd`#egg=raven-aiohttp[test]"

test: develop lint-python test-python

test-python:
	@echo "--> Running Python tests"
	python setup.py test
	@echo ""

lint-python:
	@echo "--> Linting Python files"
	flake8 --show-source setup.py raven_aiohttp.py
	isort --check-only setup.py raven_aiohttp.py --diff
	flake8 --show-source tests
	isort --check-only -rc tests --diff
	@echo ""
