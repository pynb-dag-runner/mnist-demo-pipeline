SHELL := /bin/bash

# --- Tasks to build Docker images ---

build-base-env-docker-image:
	docker \
	    build \
	    --file Dockerfile.base \
	    --build-arg HOST_UID=$$(id -u) \
	    --build-arg HOST_GID=$$(id -g) \
	    --tag mnist-demo-pipeline-base \
	    .

build-cicd-env-docker-image:
	# (Below docker context is mnist-demo-pipeline repo root so we can access
	# wheel-file built into pynb-dag-runner submodule.)
	docker \
	    build \
	    --no-cache \
	    --file Dockerfile.cicd \
	    --tag mnist-demo-pipeline-cicd \
	    ..

JUPYTER_TOKEN:
	# Create random JUPYTER_TOKEN for Jupyter running in Docker
	openssl rand -base64 42 > JUPYTER_TOKEN

build-dev-env-docker-image: JUPYTER_TOKEN
	docker \
	    build \
	    --file Dockerfile.dev \
	    --build-arg JUPYTER_TOKEN=$$(cat JUPYTER_TOKEN) \
	    --tag mnist-demo-pipeline-local-dev \
	    .
