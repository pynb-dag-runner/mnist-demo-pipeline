from pathlib import Path

#
import numpy as np

#
from common.io import (
    write_numpy,
    read_numpy,
    datalake_root,
    read_onnx,
    write_onnx,
    get_onnx_inputs,
    get_onnx_outputs,
)

def test_imports():

    # this is causing problem 1/2023 in summary notebook
    from pynb_dag_runner.tasks.task_opentelemetry_logging import (
        PydarLogger,
        get_logged_values,
    )
    from pynb_dag_runner.opentelemetry_helpers import _get_all_spans, Spans

def test_datalake_root():
    P = {"pipeline.data_lake_root": "/foo/bar"}

    assert datalake_root(P) == Path("/foo/bar")


def test_numpy_read_write(tmp_path: Path):
    filepath = tmp_path / "foo" / "bar" / "baz.numpy"
    assert not filepath.is_file()

    v1 = np.random.rand(1, 2, 3, 4)
    assert v1.shape == (1, 2, 3, 4)
    write_numpy(filepath, v1)
    assert filepath.is_file()

    v2 = read_numpy(filepath)
    assert v1.shape == v2.shape
    assert (v1 == v2).all()


def test_onnx_io_for_a_svc_model(tmp_path: Path):
    from sklearn.svm import SVC

    # Step 1: create synthetic train data for multiclass classification problem
    def get_X_y():
        samples_a = 10
        samples_b = 20
        samples_c = 30
        N = samples_a + samples_b + samples_c

        X = np.array(samples_a * [[1, 0]] + samples_b * [[0, 1]] + samples_c * [[0, 2]])
        y = np.array(samples_a * [0] + samples_b * [1] + samples_c * [2])

        assert X.shape == (N, 2)
        assert y.shape == (N,)
        return X, y

    # Step 2: train a sklearn support vector machine model on this data
    def get_trained_model(X, y):
        model = SVC(C=1, kernel="linear", probability=True)
        model.fit(X, y)
        return model

    X, y = get_X_y()
    model = get_trained_model(X, y)

    # Step 3: predict outcomes (hard labels and probabilities) using the sklearn model
    sk_pred_labels = np.array(model.predict(X))
    sk_pred_probabilities = np.array(model.predict_proba(X))

    def get_onnx_inference_session(model):
        """
        For an input sklearn model:
         - convert the sklearn model into ONNX,
         - persist the ONNX-model,
         - load the persisted ONNX model,
         - return the loaded ONNX model.
        """
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType

        # None in FloatTensorType means batch size is unknown, see
        # https://onnx.ai/sklearn-onnx/api_summary.html
        model_onnx = convert_sklearn(
            model, initial_types=[("float_input", FloatTensorType([None, 2]))]
        )

        model_path: Path = tmp_path / "models-dir" / "model.onnx"
        write_onnx(model_path, model_onnx)
        onnx_inference_session = read_onnx(model_path)

        assert get_onnx_inputs(onnx_inference_session) == [
            {"name": "float_input", "shape": [None, 2], "type": "tensor(float)"}
        ]
        assert get_onnx_outputs(onnx_inference_session) == [
            {"name": "output_label", "shape": [None], "type": "tensor(int64)"},
            {
                "name": "output_probability",
                "shape": [],
                "type": "seq(map(int64,tensor(float)))",
            },
        ]
        return onnx_inference_session

    # Step 4: get output predictions of persisted-and-loaded ONNX model on train data
    onnx_pred_labels, onnx_pred_probabilities_map = get_onnx_inference_session(
        model
    ).run(
        ["output_label", "output_probability"],
        {"float_input": X.astype(np.float32)},
    )

    # Step 5: assert that the two models gives same results

    # a) assert that predicted labels are equal
    assert sk_pred_labels.shape == onnx_pred_labels.shape == y.shape
    assert (sk_pred_labels == y).all()
    assert (onnx_pred_labels == y).all()

    # b) assert that predicted probabilities are equal
    onnx_pred_probabilities = np.array(
        [[entry[k] for k in range(3)] for entry in onnx_pred_probabilities_map]
    )
    assert sk_pred_probabilities.shape == onnx_pred_probabilities.shape
    assert np.allclose(
        sk_pred_probabilities, onnx_pred_probabilities, atol=1e-6, rtol=0
    )
