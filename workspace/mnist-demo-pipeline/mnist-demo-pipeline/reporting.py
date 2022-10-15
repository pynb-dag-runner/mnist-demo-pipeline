import json
from pathlib import Path
from functools import lru_cache


@lru_cache
def args():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "--pipeline_outputs_path",
        type=Path,
        help="output path where OpenTelemetry spans have been expanded (tmp)",
    )

    return parser.parse_args()


print(f"--- Command line parameters")
print(f"  - pipeline_outputs_path         : {args().pipeline_outputs_path}")


def get_url_to_this_run(pipeline_outputs_path: Path) -> str:
    pipeline_attributes = json.loads(
        (pipeline_outputs_path / "pipeline.json").read_text()
    )["attributes"]

    repo_owner, repo_name = pipeline_attributes["pipeline.github.repository"].split("/")
    run_id = pipeline_attributes["pipeline.pipeline_run_id"]

    return f"https://{repo_owner}.github.io/{repo_name}/#/experiments/all-pipelines-runs/runs/{run_id}"


def make_markdown_report(pipeline_outputs_path: Path) -> str:
    report_lines = []

    runlink = get_url_to_this_run(pipeline_outputs_path)
    report_lines.append(
        f"Inspect details on this pipeline run: [Github Pages link]({runlink})"
    )
    report_lines.append("")

    report_lines.append("## DAG diagram of task dependencies in this pipeline")
    report_lines.append("```mermaid")
    report_lines.append((pipeline_outputs_path / "dag.mmd").read_text())
    report_lines.append("```")
    report_lines.append("Click on a task for more details.")

    report_lines.append("## Gantt diagram of task runs in pipeline")
    report_lines.append("```mermaid")
    report_lines.append((pipeline_outputs_path / "gantt.mmd").read_text())
    report_lines.append("```")
    report_lines.append("---")
    report_lines.append(
        "Note: the above links point to a static Github Pages site built using build artifacts "
        "for this repo. The links will only work (1) after the static site has been built, and "
        "(2) if the build artifacts existed when the site was last built. "
        "Since Github Build artifacts has maximum retention period of 90 days, the "
        "links will not work forever."
    )

    return "\n".join(report_lines)


(args().pipeline_outputs_path / "pipeline_run_summary.md").write_text(
    make_markdown_report(args().pipeline_outputs_path)
)


print("--- Done ---")
