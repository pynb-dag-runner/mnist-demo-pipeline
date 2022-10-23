SHELL := /bin/bash


# --- Tasks to build Docker images ---

build-base-env-docker-image:
	docker build \
	    --file Dockerfile.base \
	    --build-arg HOST_UID=$$(id -u) \
	    --build-arg HOST_GID=$$(id -g) \
	    --tag mnist-demo-pipeline-base \
	    .

build-cicd-env-docker-image:
	docker build \
	    --file Dockerfile.cicd \
	    --tag mnist-demo-pipeline-cicd \
	    .

JUPYTER_TOKEN:
	@echo "Creating random JUPYTER_TOKEN for logging into Jupyter running in Docker ..."
	openssl rand -base64 42 > JUPYTER_TOKEN

build-local-dev-env-docker-image: JUPYTER_TOKEN
	docker build \
	    --file Dockerfile.local-dev \
	    --build-arg JUPYTER_TOKEN=$$(cat JUPYTER_TOKEN) \
	    --tag mnist-demo-pipeline-local-dev \
	    .

build-all-docker-images:
	$(MAKE) build-base-env-docker-image
	$(MAKE) build-cicd-env-docker-image
	$(MAKE) build-local-dev-env-docker-image


# --- Run commands in Docker images ---

in-cicd-docker/run-command:
	docker run --rm --tty \
	    --env RUN_ENVIRONMENT=$(RUN_ENVIRONMENT) \
	    $(EXTRA_FLAGS) \
	    --volume $$(pwd)/../workspace:/home/host_user/workspace \
	    --volume $$(pwd)/../pipeline-outputs:/pipeline-outputs \
	    --workdir /home/host_user/workspace/ \
	    mnist-demo-pipeline-cicd \
	    "$(COMMAND)"


# --- Manually start/stop the dev-docker container (without VS Code) ---

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
