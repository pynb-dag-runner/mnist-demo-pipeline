from pathlib import Path

# -
from sklearn import datasets

# -
from pynb_dag_runner.wrappers import task, TaskContext

# -
from common.io import datalake_root, write_numpy


@task(task_id="ingest", timeout_s=30.0, num_cpus=1)
def ingest(C: TaskContext):
    """
    Ingest toy version of MNIST digit data from sklearn

    """
    digits = datasets.load_digits()

    X = digits["data"]
    y = digits["target"]

    C.log_value("data_shape", list(X.shape))
    C.log_value("target_shape", list(y.shape))

    datalake_root = Path(C.parameters["workflow.data_lake_root"])
    write_numpy(datalake_root / "raw" / "digits.numpy", X)
    write_numpy(datalake_root / "raw" / "labels.numpy", y)

    return 123
