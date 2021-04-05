
.PHONY: install-linting
install-linting:
	pip install -r tests/requirements-linting.txt
	# log installs
	pip freeze

.PHONY: lint
lint: install-linting
	# stop the build if there are Python syntax errors or undefined names
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	mypy src/pyopenapi3

.PHONY: install-pyopenapi3
install-pyopenapi3:
	python -m pip install -U wheel pip
	pip install -r requirements.txt
	pip install -e .

.PHONY: install-testing
install-testing: install-pyopenapi3
	pip install -r tests/requirements-testing.txt
	# log installs
	pip freeze

.PHONY: test
test: install-testing
	pytest -vv

.PHONY: connexion-example
connexion-example: install-pyopenapi3
	pip install -r examples/connexion_example/conn-ex-requirements.txt
	python examples/connexion_example/app.py

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

