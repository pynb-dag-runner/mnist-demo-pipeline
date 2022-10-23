.PHONY: *
SHELL := /bin/bash

install-editable:
	@# Installing mnist-demo-pipeline common package in editable mode ...
	pip3 install --user --editable .

clean:
	rm -rf mnist_demo_pipeline_common.egg-info


# --- test related tasks ---

test-pytest:
	@echo ">>> $$(date): Running pytest unit tests ..."
	pytest tests

test-mypy:
	@echo ">>> $$(date): Running mypy static type checking ..."
	mypy --ignore-missing-imports .

test-black:
	@echo ">>> $$(date): Verify that code is black formatted ..."
	black --check --diff .

# --- Define the below tasks for running tests in watch mode:
#       watch-test-pytest
#       watch-test-mypy
#       watch-test-black

watch-%:
	@find . \
	    | grep ".py" \
	    | entr \
	    $(MAKE) --no-print-directory $*

tmux-run-all-tests-in-watch-mode:
	@echo ">>> Running all tests in watch mode. "
	@echo " - Exit with <Ctrl-B> + 'X'"
	@tmuxinator start
