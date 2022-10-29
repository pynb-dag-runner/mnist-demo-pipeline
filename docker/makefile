SHELL                   := /bin/bash
DOCKER_IMAGE_NAME       := mnist-demo-pipeline
BUILT_DOCKER_LOCK_FILE  := ./.built-docker-images/${DOCKER_IMAGE_NAME}


# --- Tasks to build Docker images ---

${BUILT_DOCKER_LOCK_FILE}-base: Dockerfile.base makefile
	docker build \
	    --no-cache \
	    --file Dockerfile.base \
	    --build-arg HOST_UID=$$(id -u) \
	    --build-arg HOST_GID=$$(id -g) \
	    --tag ${DOCKER_IMAGE_NAME}-base \
	    .
	mkdir -p $(shell dirname $@)
	touch $@

${BUILT_DOCKER_LOCK_FILE}-cicd: ${BUILT_DOCKER_LOCK_FILE}-base Dockerfile.cicd makefile
	docker build \
	    --no-cache \
	    --file Dockerfile.cicd \
	    --tag ${DOCKER_IMAGE_NAME}-cicd \
	    .
	mkdir -p $(shell dirname $@)
	touch $@

JUPYTER_TOKEN:
	@echo "Creating random JUPYTER_TOKEN for logging into Jupyter running in Docker ..."
	openssl rand -base64 42 > JUPYTER_TOKEN

${BUILT_DOCKER_LOCK_FILE}-dev: JUPYTER_TOKEN ${BUILT_DOCKER_LOCK_FILE}-cicd makefile
	docker build \
	    --no-cache \
	    --file Dockerfile.local-dev \
	    --build-arg JUPYTER_TOKEN=$(shell cat JUPYTER_TOKEN) \
	    --tag ${DOCKER_IMAGE_NAME}-local-dev \
	    .
	mkdir -p $(shell dirname $@)
	touch $@

build-all-docker-images: ${BUILT_DOCKER_LOCK_FILE}-dev


# --- Run a command in Docker images ---

in-cicd-docker/run-command: ${BUILT_DOCKER_LOCK_FILE}-cicd
	docker run \
	    --rm \
	    --tty \
	    ${EXTRA_FLAGS} \
	    --volume $(shell pwd)/../workspace:/home/host_user/workspace \
	    --volume $(shell pwd)/../pipeline-outputs:/pipeline-outputs \
	    --workdir /home/host_user/workspace/ \
	    ${DOCKER_IMAGE_NAME}-cicd \
	    "${COMMAND}"
