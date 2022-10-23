.PHONY: *
SHELL := /bin/bash

install-editable:
	@# Installing mnist-demo-pipeline common package in editable mode ...
	pip3 install --user --editable .

clean:
	rm -rf mnist_demo_pipeline_common.egg-info

test-pytest:
	pytest tests

test-mypy:
	mypy --ignore-missing-imports .

test-black:
	black --check --diff .
