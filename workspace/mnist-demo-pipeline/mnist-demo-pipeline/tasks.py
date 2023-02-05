from pathlib import Path

# -
from sklearn import datasets
from sklearn.model_selection import train_test_split

# -
from pynb_dag_runner.wrappers import task, TaskContext

# -
from common.io import read_numpy, write_numpy


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

    return {"X": X, "y": y}


@task(task_id="split_train_test", timeout_s=30.0, num_cpus=1)
def split_train_test(train_test_ratio: float, ingested_data, C: TaskContext):
    """
    Split digits and labels into separate training and testing data sets
    """
    X = ingested_data["X"]
    y = ingested_data["y"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        train_size=train_test_ratio,
        test_size=None,
        stratify=y,
        shuffle=True,
        random_state=1,
    )

    # assert nr of pixels per image is the same for all image vectors
    assert X.shape[1] == X_train.shape[1] == X_test.shape[1]

    # assert that the (X, y)-pairs have compatible sizes (for both train and test)
    assert X_train.shape[0] == len(y_train)
    assert X_test.shape[0] == len(y_test)

    # assert that all data is used
    assert len(y) == len(y_train) + len(y_test)

    C.log_int("nr_digits_train", len(y_train))
    C.log_int("nr_digits_test", len(y_test))

    # Persist training and test data sets to separate files
    datalake_root = Path(C.parameters["workflow.data_lake_root"])
    write_numpy(datalake_root / "train-data" / "digits.numpy", X_train)
    write_numpy(datalake_root / "train-data" / "labels.numpy", y_train)

    write_numpy(datalake_root / "test-data" / "digits.numpy", X_test)
    write_numpy(datalake_root / "test-data" / "labels.numpy", y_test)
