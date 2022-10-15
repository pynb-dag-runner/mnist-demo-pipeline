.PHONY: *
SHELL := /bin/bash

run-pipeline:
	@echo "*** Running pipeline ..."
	@echo " - environment variable RUN_ENVIRONMENT: ${RUN_ENVIRONMENT}"
	(cd mnist-demo-pipeline; \
	    python3 -u driver.py \
	        --data_lake_root /pipeline-outputs/data-lake \
	        --otel_spans_outputfile /pipeline-outputs/opentelemetry-spans.json \
	        --run_environment ${RUN_ENVIRONMENT} \
	)

add-run-summary:
	@echo "*** Create summary of pipeline run"
	(\
	    cd mnist-demo-pipeline; \
	    python3 -u \
	        reporting.py \
	        --pipeline_outputs_path ${PIPELINE_OUTPUTS_PATH} \
	)

expand-opentelemetry-spans-into-directory-structure:
	@echo "*** Expanding pipeline OpenTelemetry spans into a directory structure for manual inspection ..."
	pynb_log_parser \
	    --input_span_file /pipeline-outputs/opentelemetry-spans.json \
	    --output_directory /pipeline-outputs \
	    --output_filepath_mermaid_gantt /pipeline-outputs/gantt.mmd \
	    --output_filepath_mermaid_dag /pipeline-outputs/dag.mmd

test-mypy:
	mypy --ignore-missing-imports .

test-black:
	black --check --diff --exclude /.ipynb_checkpoints/ .

clean-pipeline-outputs:
	# use with care
	rm -rf /pipeline-outputs/*
	touch /pipeline-outputs/.gitkeep
