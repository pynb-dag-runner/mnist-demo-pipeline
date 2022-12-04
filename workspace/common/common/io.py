import os
from pathlib import Path

#
import numpy as np
import onnx

from onnxruntime.capi.onnxruntime_inference_collection import InferenceSession
import onnxruntime as rt

# See: https://github.com/microsoft/onnxruntime/blob/master/docs/Privacy.md
rt.disable_telemetry_events()
rt.set_seed(0)


def datalake_root(P):
    return Path(P["pipeline.data_lake_root"])


def write_numpy(path: Path, numpy_obj):
    """
    Serialize and write a numpy array to a local file
    """
    if path.suffix == ".numpy":
        raise ValueError(f"Path {path} should have .numpy suffix!")

    # Create local directory for file if it does not exist
    os.makedirs(path.parent, exist_ok=True)

    with open(path, "wb") as f:
        np.save(f, numpy_obj, allow_pickle=False)


def read_numpy(path: Path):
    """
    Read numpy array from a local file saved with write_numpy, see above
    """

    if path.suffix == ".numpy":
        raise ValueError(f"Path {path} should have .numpy suffix!")

    if not path.is_file():
        raise ValueError(f"Path {path} does not exist!")

    with open(path, "rb") as f:
        return np.load(f)


# ---- onnx helpers for persisting and loading ml models, see https://onnx.ai ----


def write_onnx(path: Path, model_onnx: onnx.onnx_ml_pb2.ModelProto):
    os.makedirs(path.parent, exist_ok=True)

    path.write_bytes(model_onnx.SerializeToString())


def read_onnx(path: Path) -> InferenceSession:
    if not path.is_file():
        raise ValueError(f"Path {path} does not exist!")

    rt.set_seed(0)
    return rt.InferenceSession(path.read_bytes())


def get_onnx_inputs(onnx_inference_session: InferenceSession):
    """
    Return a list describing the input parameters for an ONNX model
    """
    return [
        {"name": input.name, "shape": input.shape, "type": input.type}
        for input in onnx_inference_session.get_inputs()
    ]


def get_onnx_outputs(onnx_inference_session: InferenceSession):
    """
    Return a list describing the outputs from an ONNX model
    """
    return [
        {"name": output.name, "shape": output.shape, "type": output.type}
        for output in onnx_inference_session.get_outputs()
    ]
