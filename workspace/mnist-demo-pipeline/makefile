.PHONY: *
SHELL := /bin/bash

run-pipeline:
	@echo "*** Running pipeline ... ***"
	@echo " - environment variable RUN_ENVIRONMENT: ${RUN_ENVIRONMENT}"
	( \
	    cd mnist-demo-pipeline; \
	    python3 -u driver.py \
	        --data_lake_root /pipeline-outputs/data-lake \
	        --otel_spans_outputfile /pipeline-outputs/opentelemetry-spans.json \
	        --run_environment ${RUN_ENVIRONMENT} \
	)

add-run-summary:
	@echo "*** Create summary of pipeline run ... ***"
	( \
	    cd mnist-demo-pipeline; \
	    python3 -u \
	        reporting.py \
	        --pipeline_outputs_path ${PIPELINE_OUTPUTS_PATH} \
	)

expand-opentelemetry-spans-into-directory-structure:
	@echo "*** Expanding pipeline OpenTelemetry spans into a directory structure for manual inspection ... ***"
	pynb_log_parser \
	    --input_span_file               /pipeline-outputs/opentelemetry-spans.json \
	    --output_directory              /pipeline-outputs/pipeline-outputs \
	    --output_filepath_mermaid_gantt /pipeline-outputs/gantt.mmd \
	    --output_filepath_mermaid_dag   /pipeline-outputs/dag.mmd
	@echo "- done"

local-dev-run-pipeline:
	@# TODO: move steps into driver where it makes sense (it has all parameters)
	$(MAKE) run-pipeline RUN_ENVIRONMENT=dev

	# Skip summary for local-dev, since this step depends on environment variables only
	# set in Github
	# $(MAKE) add-run-summary PIPELINE_OUTPUTS_PATH=/pipeline-outputs/
	$(MAKE) expand-opentelemetry-spans-into-directory-structure

test-mypy:
	@echo ">>> $(shell date): Verifying type hints in pipeline notebooks ..."
	mypy --ignore-missing-imports .

test-black:
	@echo ">>> $(shell date): Verify that notebooks are black formatted ..."
	black --check --diff --exclude /.ipynb_checkpoints/ .

# --- Define the below tasks for running pipeline in watch mode for local dev ---
#       watch-local-dev-run-pipeline
#       watch-test-mypy
#       watch-test-black

watch-%:
	@find . \
	    | grep ".py" \
	    | entr \
	    $(MAKE) --no-print-directory $*

tmux-watch-pipeline-and-static-tests:
	@echo ">>> Running all tests in watch mode. "
	@echo " - Exit with <Ctrl-B> + X"
	@tmuxinator start
