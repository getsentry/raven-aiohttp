develop:
	@echo "--> Installing dependencies"
	pip install -e .
	pip install "file://`pwd`#egg=raven-aiohttp[test]"

test: develop lint-python test-python

test-python:
	@echo "--> Running Python tests"
	py.test test_raven_aiohttp.py
	@echo ""

lint-python:
	@echo "--> Linting Python files"
	PYFLAKES_NODOCTEST=1 flake8 *.py
	@echo ""
