from typing import Optional

#
import json
from pathlib import Path

#
from pynb_dag_runner import version_string
from pynb_dag_runner.opentelemetry_helpers import Spans
from pynb_dag_runner.opentelemetry_task_span_parser import parse_spans

from otel_output_parser.mermaid_graphs import (
    make_mermaid_dag_inputfile,
    make_mermaid_gantt_inputfile,
)


def args():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "--input_otel_spans_json_file",
        type=Path,
        help="input filepath with logged spans (as an OpenTelemetry JSON file) for pipeline run",
    )
    parser.add_argument(
        "--output_markdown_file",
        type=Path,
        help="filepath where to write output markdown report",
    )

    return parser.parse_args()


def load_spans() -> Spans:
    return Spans(json.loads(args().input_otel_spans_json_file.read_text()))


def get_pipeline_attributes(spans: Spans):
    return parse_spans(spans).attributes


def is_remote_run(spans: Spans) -> bool:
    """
    Where the logged spans executed on Github?
    """
    return {
        "workflow.github.repository",
        "workflow.workflow_run_id",
    } <= get_pipeline_attributes(spans).keys()


print(f"--- demo pipeline reporting {version_string()} ---")
print(f"  - input_otel_spans_json_file  : {args().input_otel_spans_json_file}")
print(f"  - output_markdown_file        : {args().output_markdown_file}")


def get_url_to_this_run(spans: Spans) -> Optional[str]:
    assert is_remote_run(spans)

    pipeline_attributes = get_pipeline_attributes(spans)

    repo_owner, repo_name = pipeline_attributes["workflow.github.repository"].split("/")
    run_id = pipeline_attributes["workflow.workflow_run_id"]

    return f"https://{repo_owner}.github.io/{repo_name}/#/experiments/all-workflow-runs/runs/{run_id}"


def make_markdown_report(spans: Spans) -> str:
    remote_run: bool = is_remote_run(spans)
    report_lines = []

    #
    if remote_run:
        runlink = get_url_to_this_run(spans)
        report_lines.append(
            f"Inspect details on this pipeline run: [Github Pages link]({runlink})"
        )
        report_lines.append("")

    # Add DAG diagram
    report_lines.append("## DAG diagram of task dependencies in this pipeline")
    report_lines.append("```mermaid")
    report_lines.append(make_mermaid_dag_inputfile(spans, generate_links=remote_run))
    report_lines.append("```")

    if remote_run:
        report_lines.append("Click on a task for more details.")

    # Add Gantt diagram
    report_lines.append("## Gantt diagram of task runs in pipeline")
    report_lines.append("```mermaid")
    report_lines.append(make_mermaid_gantt_inputfile(spans))
    report_lines.append("```")
    report_lines.append("---")

    if remote_run:
        report_lines.append(
            "Note: the above links point to a static Github Pages site built using "
            "build artifacts for this repo. The links will only work "
            "(1) after the static site has been built, and "
            "(2) if the build artifacts existed when the site was last built. "
            "Since Github Build artifacts has maximum retention period of 90 days, "
            "the links will not work forever."
        )

    return "\n".join(report_lines)


args().output_markdown_file.write_text(
    make_markdown_report(load_spans()),
)


print("--- Done ---")
