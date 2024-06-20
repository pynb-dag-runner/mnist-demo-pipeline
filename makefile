.PHONY: *
SHELL := /bin/bash

# override when invoking make, eg "make RUN_ENVIRONMENT=ci ..."
RUN_ENVIRONMENT ?= "dev"

# --- Docker related tasks ---

build-all-docker-images:
	(cd docker; make build-all-docker-images)

# --- Pipeline tasks ---

clean:
	@# The below does not run in Docker since we are just deleting files

	@echo " *** Cleaning any built artifacts for common Python package ..."
	@(cd workspace/common; $(MAKE) clean)

	@echo " *** Emptying pipeline-outputs directory ..."
	@rm -rf pipeline-outputs/*
	@touch pipeline-outputs/.gitkeep


in-cicd-docker/test-and-run-pipeline: | clean
	@# Single command to run all tests, run the pipeline and expand output into directory structure
	cd docker; \
	$(MAKE) in-cicd-docker/run-command \
	    EXTRA_FLAGS=" \
	        --network none \
	        --env RUN_ENVIRONMENT=${RUN_ENVIRONMENT} \
	    " \
	    COMMAND="( \
	        cd common; \
	        make install-editable; \
	        make test-pytest test-mypy test-black; \
	        make clean; \
	    ) && ( \
	        cd mnist-demo-pipeline; \
	        make test-mypy test-black; \
	        make run-pipeline; \
	        make expand-opentelemetry-spans-into-directory-structure; \
	    )"
