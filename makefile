.PHONY: *
SHELL := /bin/bash

# override when invoking make, eg "make RUN_ENVIRONMENT=ci ..."
RUN_ENVIRONMENT ?= "dev"

# --- Docker related tasks ---

build-all-docker-images:
	(cd docker; make build-all-docker-images)

### Manually start/stop the dev-docker container (can be used without VS Code)

dev-up:
	docker-compose \
	    -f .devcontainer-docker-compose.yml \
	    up \
	    --remove-orphans \
	    --abort-on-container-exit \
	    dev-environment

dev-down:
	docker-compose \
	    -f .devcontainer-docker-compose.yml \
	    down \
	    --remove-orphans

run[in-base-docker]:
	docker run --rm --tty \
	    --env RUN_ENVIRONMENT=$(RUN_ENVIRONMENT) \
	    $(EXTRA_FLAGS) \
	    --volume $$(pwd)/workspace:/home/host_user/workspace \
	    --volume $$(pwd)/pipeline-outputs:/pipeline-outputs \
	    --workdir /home/host_user/workspace/ \
	    mnist-demo-pipeline-base \
	    "$(COMMAND)"

docker-run-in-cicd:
	docker run --rm --tty \
	    --env RUN_ENVIRONMENT=$(RUN_ENVIRONMENT) \
	    $(EXTRA_FLAGS) \
	    --volume $$(pwd)/workspace:/home/host_user/workspace \
	    --volume $$(pwd)/pipeline-outputs:/pipeline-outputs \
	    --workdir /home/host_user/workspace/ \
	    mnist-demo-pipeline-cicd \
	    "$(COMMAND)"

# --- pipeline tasks ---

clean:
	# The below commands do not depend on RUN_ENVIRONMENT. But, the command
	# is most useful in dev-setup.
	$(MAKE) docker-run-in-cicd \
	    COMMAND="( \
	        cd common; make clean; \
	        cd mnist-demo-pipeline; make clean-pipeline-outputs; \
	    )"

test-and-run-pipeline[in-docker]: | clean
	# Single command to run all tests, run the pipeline and expand output into directory structure

	$(MAKE) docker-run-in-cicd \
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
