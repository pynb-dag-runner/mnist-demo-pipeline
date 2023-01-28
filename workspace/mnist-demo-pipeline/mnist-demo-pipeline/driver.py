from pathlib import Path
import uuid, shutil
from functools import lru_cache
from typing import List

#
import ray

#
from pynb_dag_runner import version_string
from pynb_dag_runner.tasks.tasks import make_jupytext_task
from pynb_dag_runner.opentelemetry_helpers import SpanRecorder
from pynb_dag_runner.run_pipeline_helpers import get_github_env_variables
from pynb_dag_runner.notebooks_helpers import JupytextNotebookContent

from pynb_dag_runner.helpers import write_json
from pynb_dag_runner.wrappers import task, run_dag

print(f"--- Running: demo-train-mnist-ml-model-pipeline ---")
print(f"--- Initialize Ray cluster ---")

# Setup Ray and enable tracing using default OpenTelemetry support; traces are
# written to files /tmp/spans/<pid>.txt in JSON format.
shutil.rmtree("/tmp/spans", ignore_errors=True)
ray.init(_tracing_startup_hook="ray.util.tracing.setup_local_tmp_tracing:setup_tracing")

print("--- Determining input and context variables ---")
print(f"  - Composable Logs version {version_string()}")


@lru_cache
def args():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "--otel_spans_outputfile",
        type=str,
        help="output file path where to write logged OpenTelemetry spans for this pipeline run",
    )
    parser.add_argument(
        "--data_lake_root",
        type=str,
        help="output local directory where to write data artefacts (typically written to a data lake)",
    )
    parser.add_argument(
        "--run_environment",
        type=str,
        choices=["ci", "dev"],
        help="run environment",
    )

    return parser.parse_args()


GLOBAL_PARAMETERS = {
    # data lake root is pipeline-scoped parameter
    "workflow.data_lake_root": args().data_lake_root,
    "workflow.run_environment": args().run_environment,
    "workflow.workflow_run_id": str(uuid.uuid4()),  # TODO: replace with top span
    **get_github_env_variables(),
}


NR_TRAIN_IMAGES_LIST: List[int] = []

if args().run_environment == "ci":
    NR_TRAIN_IMAGES_LIST = [600, 800, 1000, 1200]
elif args().run_environment == "dev":
    NR_TRAIN_IMAGES_LIST = [400, 500, 600]
else:
    raise ValueError(f"Unknown environment {args().run_environment}")


print(f"--- cli arguments ---")
print(f"  - otel_spans_outputfile           : {args().otel_spans_outputfile}")
print(f"  - data_lake_root                  : {args().data_lake_root}")
print(f"  - run_environment                 : {args().run_environment}")
print(f"  - training for training set sizes : {NR_TRAIN_IMAGES_LIST}")


print("--- Setting up tasks and task dependencies ---")

# Note: the below steps does not start any computation.
# They only set up the compute dag.


def get_notebook(notebook_filename: str) -> JupytextNotebookContent:
    return JupytextNotebookContent(
        filepath=notebook_filename,
        content=(Path(__file__).parent / "notebooks" / notebook_filename).read_text(),
    )


task_ingest = make_jupytext_task(
    notebook=get_notebook("ingest.py"),
    timeout_s=600.0,
    num_cpus=2,
    parameters=GLOBAL_PARAMETERS,
)()

task_eda = make_jupytext_task(
    notebook=get_notebook("eda.py"),
    parameters=GLOBAL_PARAMETERS,
)(task_ingest)

task_split_train_test = make_jupytext_task(
    notebook=get_notebook("split-train-test.py"),
    parameters={
        **GLOBAL_PARAMETERS,
        "task.train_test_ratio": 0.7,
    },
)(task_ingest)


def make_train_and_benchmark_model_task(nr_train_images):
    task_parameters = {**GLOBAL_PARAMETERS, "task.nr_train_images": nr_train_images}
    task_train = make_jupytext_task(
        notebook=get_notebook("train-model.py"),
        timeout_s=120.0,
        num_cpus=1,
        parameters=task_parameters,
    )

    task_benchmark = make_jupytext_task(
        notebook=get_notebook("benchmark-model.py"),
        parameters=task_parameters,
    )

    return task_benchmark(task_train(task_split_train_test))


# run summary job after all train_and_benchmark tasks have finished
task_summary = make_jupytext_task(notebook=get_notebook("summary.py"), parameters={})(
    *[make_train_and_benchmark_model_task(k) for k in NR_TRAIN_IMAGES_LIST]
)


dag_tasks_to_await = [task_eda, task_summary]


print("--- Start computation of the mnist-demo-trainer workflow ---")

with SpanRecorder() as rec:
    run_dag(dag_tasks_to_await)

ray.shutdown()

print("--- Exceptions ---")

for s in rec.spans.exception_events():
    print(80 * "=")
    print(s)

print("--- Writing spans ---")

print(" - Total number of spans recorded   :", len(rec.spans))
write_json(Path(args().otel_spans_outputfile), list(rec.spans))

print("--- Done ---")
