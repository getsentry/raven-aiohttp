develop:
	@echo "--> Installing dependencies"
	pip install -e .
	pip install "file://`pwd`#egg=raven-aiohttp[test]"
	pip install docutils

test: develop lint-python test-python test-setup

test-python:
	@echo "--> Running Python tests"
	py.test test_raven_aiohttp.py
	@echo ""

test-setup:
	@echo "--> Running test-check"
	python setup.py check -r -s

lint-python:
	@echo "--> Linting Python files"
	PYFLAKES_NODOCTEST=1 flake8 *.py
	@echo ""
