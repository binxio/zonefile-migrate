.PHONY: build
build:
	python setup.py check
	python setup.py build

test:
	python setup.py test

release:
	rm -rf dist/*
	python setup.py sdist
	twine upload dist/*

clean:
	find . -type d -name __pycache__ | xargs rm -rf
	find . -type d -name \*.egg-info | xargs rm -rf
	find . -type f -name \*.pyc | xargs rm -rf
	rm -rf build dist .eggs
