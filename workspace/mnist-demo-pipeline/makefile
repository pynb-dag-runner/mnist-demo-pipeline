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

create-pipeline-run-summary:
	@echo "*** Create pipeline run summary from OpenTelemetry JSON file ... ***"
	( \
	    cd mnist-demo-pipeline; \
	    python3 -u \
	        reporting.py \
	        --input_otel_spans_json_file ${OTEL_SPANS_OUTPUTFILE} \
	        --output_markdown_file ${OUTPUT_MARKDOWN_FILE} \
	)

expand-opentelemetry-spans-into-directory-structure:
	@echo "*** Expanding pipeline OpenTelemetry spans into a directory structure for manual inspection ... ***"
	pynb_log_parser \
	    --input_span_file               /pipeline-outputs/opentelemetry-spans.json \
	    --output_directory              /pipeline-outputs/pipeline-outputs \
	    --output_filepath_mermaid_gantt /pipeline-outputs/gantt.mmd \
	    --output_filepath_mermaid_dag   /pipeline-outputs/dag.mmd
	@echo "- done"


# ---

local-dev-run-pipeline:
	$(MAKE) run-pipeline RUN_ENVIRONMENT=dev

	$(MAKE) create-pipeline-run-summary \
	    OTEL_SPANS_OUTPUTFILE=/pipeline-outputs/opentelemetry-spans.json \
	    OUTPUT_MARKDOWN_FILE=/pipeline-outputs/summary.md

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
