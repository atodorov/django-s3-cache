test:
	PYTHONPATH=. nosetests -v --with-coverage --cover-branches --cover-erase \
	    --cover-package s3cache tests/ && coverage report -m

pylint:
	pylint -rn *.py s3cache/ tests/*.py

build: test
	./setup.py sdist

upload: test
	./setup.py sdist upload

clean:
	./setup.py clean
	rm -rf django_s3_cache.egg-info/
	rm -f MANIFEST *.pyc s3cache/*.pyc

distclean: clean
	rm -rf dist/
	rm -rf tests/__pycache__/

help:
	@echo "Usage: make <target>                   "
	@echo "                                       "
	@echo " test - run the tests                  "
	@echo " pylint - run PyLint                   "
	@echo " build - build the package             "
	@echo " upload - upload to PyPI               "
	@echo " clean - remove all build files        "
	@echo " distclean - remove all non git files  "
	@echo " help - show this help and exit        "
