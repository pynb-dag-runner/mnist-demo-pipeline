from pathlib import Path

# -
import numpy as np
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


def load_and_limit_train_data(nr_train_images: int, datalake_root: Path):
    """
    Load and limit train data

    Steps:
     - Load all training data (images and labels).
     - Limit number of train images to `task.nr_train_images` (value provided as run parameter).
     - Train a support vector machine model using sklearn.
     - Persist the trained model using the ONNX format.

    """
    from sklearn.model_selection import train_test_split

    X_train_all = read_numpy(datalake_root / "train-data" / "digits.numpy")
    y_train_all = read_numpy(datalake_root / "train-data" / "labels.numpy")

    # Note: train_test_split will fail if split is 0 or 100%.
    assert 0 < nr_train_images < len(y_train_all)

    X_train, _, y_train, _ = train_test_split(
        X_train_all,
        y_train_all,
        train_size=nr_train_images,
        test_size=None,
        stratify=y_train_all,
        shuffle=True,
        random_state=123,
    )

    assert X_train.shape == (len(y_train), 8 * 8)

    return {"X": X_train, "y": y_train}


@task(task_id="train_model", timeout_s=60.0, num_cpus=1)
def train_model(nr_train_images: int, train_split, C: TaskContext):
    """
    Train support vector classifier model

    Below we assume that the hyperparameter $C$ is known.

    However, this should ideally be found by a hyperparameter search. That could be
    done in parallel on the Ray cluster, but this needs some more work. Ie., to use
    multiple cores in the notebook, those cores should be reserved when starting the
    notebook task.

    https://docs.ray.io/en/latest/tune/key-concepts.html

    Note: cv-scores would need to be computed here, since they depend on the train data.
    After this notebook only the onnx-model is available.
    """
    from sklearn.svm import SVC
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType

    from common.io import write_onnx

    datalake_root = Path(C.parameters["workflow.data_lake_root"])

    train = load_and_limit_train_data(nr_train_images, datalake_root)
    X_train, y_train = train["X"], train["y"]

    model = SVC(C=0.001, kernel="linear", probability=True)

    model.fit(X_train, y_train)

    # # Q: Can the labels returned by `predict(..)` be computed from probabilities
    # returned by the `predict_prob`-method?
    y_train_labels = model.predict(X_train)
    y_train_probabilities = model.predict_proba(X_train)
    assert y_train_probabilities.shape == (len(y_train), 10)

    y_train_max_prob_labels = np.argmax(y_train_probabilities, axis=1)
    assert y_train_labels.shape == y_train_max_prob_labels.shape == y_train.shape

    # If the predicted labels would coincide with the labels that have
    # maximum probability, the below number would be zero. Typically it is not.
    C.log_int(
        "nr_max_prob_neq_label", int(sum(y_train_max_prob_labels != y_train_labels))
    )

    # The explanation is (likely) explained in the SVC source, see
    # [here](https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/svm/_base.py).
    # Namely, the outputs from `predict(..)` and `predict_proba(..)` may not in some
    # cases be compatible since the latter is computed using cross-validation while
    # the former is not. Thus, the above number need not be zero.

    # --- convert sklearn model into onnx and save model both locally and to log
    model_onnx = convert_sklearn(
        model, initial_types=[("float_input_8x8_image", FloatTensorType([None, 8 * 8]))]
    )

    assert isinstance(datalake_root, Path)
    output_path: Path = (
        datalake_root / "models" / f"nr_train_images={nr_train_images}" / "model.onnx"
    )
    write_onnx(output_path, model_onnx)

    C.log_artefact("model.onnx", output_path.read_bytes())
