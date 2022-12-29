from pathlib import Path
import uuid, shutil
from functools import lru_cache
from typing import List

#
import ray

#
from pynb_dag_runner.tasks.tasks import make_jupytext_task_ot
from pynb_dag_runner.opentelemetry_helpers import SpanRecorder
from pynb_dag_runner.core.dag_runner import (
    run_in_sequence,
    fan_in,
    start_and_await_tasks,
)
from pynb_dag_runner.run_pipeline_helpers import get_github_env_variables

from pynb_dag_runner.notebooks_helpers import JupytextNotebook
from pynb_dag_runner.helpers import write_json

print("---- Initialize Ray cluster ----")

# Setup Ray and enable tracing using default OpenTelemetry support; traces are
# written to files /tmp/spans/<pid>.txt in JSON format.
shutil.rmtree("/tmp/spans", ignore_errors=True)
ray.init(_tracing_startup_hook="ray.util.tracing.setup_local_tmp_tracing:setup_tracing")


@lru_cache
def args():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "--otel_spans_outputfile",
        type=str,
        help="output file path for logging OpenTelemetry spans of pipeline run",
    )
    parser.add_argument(
        "--data_lake_root",
        type=str,
        help="local directory for data artefacts (normally written to a data lake)",
    )
    parser.add_argument(
        "--run_environment",
        type=str,
        choices=["ci", "dev"],
        help="run environment for running pipeline",
    )

    return parser.parse_args()


GLOBAL_PARAMETERS = {
    # data lake root is pipeline-scoped parameter
    "pipeline.data_lake_root": args().data_lake_root,
    "pipeline.run_environment": args().run_environment,
    "pipeline.pipeline_run_id": str(uuid.uuid4()),
    **get_github_env_variables(),
}


def make_notebook_task(nb_name: str, timeout_s=None, task_parameters={}):
    nb_path: Path = (Path(__file__).parent) / "notebooks"

    return make_jupytext_task_ot(
        notebook=JupytextNotebook(nb_path / nb_name),
        tmp_dir=nb_path,
        timeout_s=timeout_s,
        parameters={
            **GLOBAL_PARAMETERS,
            **task_parameters,
        },
    )


print("---- Command line parameters ----")
print(f"  - otel_spans_outputfile : {args().otel_spans_outputfile}")
print(f"  - data_lake_root        : {args().data_lake_root}")
print(f"  - run_environment       : {args().run_environment}")


print("---- Setting up tasks and task dependencies ----")

task_ingest = make_notebook_task(nb_name="ingest.py", timeout_s=10)

task_eda = make_notebook_task(nb_name="eda.py")
run_in_sequence(task_ingest, task_eda)

task_split_train_test = make_notebook_task(
    nb_name="split-train-test.py",
    task_parameters={"task.train_test_ratio": 0.7},
)
run_in_sequence(task_ingest, task_split_train_test)

# --- tasks defined using old API ---

nr_train_digits: List[int] = {
    "ci": [600, 800, 1000, 1200],  # list(range(600, 1201, 100)),
    "dev": [400, 500, 600],
}[args().run_environment]

task_trainers = [
    make_notebook_task(
        nb_name="train-model.py",
        task_parameters={"task.nr_train_images": k},
    )
    for k in nr_train_digits
]

task_benchmarks = [
    make_notebook_task(
        nb_name="benchmark-model.py",
        task_parameters={"task.nr_train_images": k},
    )
    for k in nr_train_digits
]

for task_train, task_benchmark in zip(task_trainers, task_benchmarks):
    run_in_sequence(task_split_train_test, task_train, task_benchmark)

task_summary = make_notebook_task(
    nb_name="summary.py",
    task_parameters={},
)

fan_in(task_benchmarks, task_summary)


print("---- Running mnist-demo-pipeline ----")

with SpanRecorder() as rec:
    _ = start_and_await_tasks(
        # Note: here it should not be necessary to await task_benchmarks. fan_in
        # target task only starts after all dependent tasks are finished, but
        # dependency logging is done in callbacks that is only awaited in source
        # tasks. TODO/check this
        [task_ingest],
        [task_eda, task_summary] + task_benchmarks,
        arg={},
    )

ray.shutdown()

print("---- Exceptions ----")

for s in rec.spans.exception_events():
    print(80 * "=")
    print(s)

print("---- Writing spans ----")

print(" - Total number of spans recorded   :", len(rec.spans))
write_json(Path(args().otel_spans_outputfile), list(rec.spans))

print("---- Done ----")
