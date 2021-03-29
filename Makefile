
.PHONY: install-linting
install-linting:
	pip install -r tests/requirements-linting.txt

.PHONY: install-pyopenapi3
install-pyopenapi3:
	python -m pip install -U wheel pip
	pip install -r requirements.txt
	pip install -e .

.PHONY: install-testing
install-testing: install-pyopenapi3
	pip install -r tests/requirements-testing.txt

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist
	python setup.py clean

