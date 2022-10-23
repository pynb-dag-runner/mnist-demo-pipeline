.PHONY: *
SHELL := /bin/bash

# override when invoking make, eg "make RUN_ENVIRONMENT=ci ..."
RUN_ENVIRONMENT ?= "dev"

# --- Docker related tasks ---

build-all-docker-images:
	(cd docker; make build-all-docker-images)

# --- pipeline tasks ---

clean:
	@# The below commands do not depend on RUN_ENVIRONMENT. But, the command
	@# is most useful in dev-setup.
	cd docker; \
	$(MAKE) in-cicd-docker/run-command \
	    COMMAND="( \
	        cd common; make clean; \
	        cd mnist-demo-pipeline; make clean-pipeline-outputs; \
	    )"

test-and-run-pipeline[in-docker]: | clean
	@# Single command to run all tests, run the pipeline and expand output into directory structure
	cd docker; \
	$(MAKE) in-cicd-docker/run-command \
	    EXTRA_FLAGS="--network none" \
	    RUN_ENVIRONMENT=$(RUN_ENVIRONMENT) \
	    COMMAND="( \
	        cd common; \
	        make install; \
	        make test-pytest test-mypy test-black; \
	        make clean; \
	    ) && ( \
	        cd mnist-demo-pipeline; \
	        make test-mypy test-black; \
	        make run-pipeline; \
	        make expand-opentelemetry-spans-into-directory-structure; \
	    )"
