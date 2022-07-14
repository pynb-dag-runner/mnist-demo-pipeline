# %% [markdown]
# # Train model
#
# The purpose of this notebook is:
#
# - Load all training data (images and labels).
# - Limit number of train images to `task.nr_train_images` (value provided as run parameter).
# - Train a support vector machine model using sklearn.
# - Persist the trained model using the ONNX format.

# %% [markdown]
# ### Determine run parameters

# %%
# ----------------- Parameters for interactive development --------------
P = {
    "pipeline.data_lake_root": "/pipeline-outputs/data-lake",
    "task.nr_train_images": 600,
}
# %% tags=["parameters"]
# - During automated runs parameters will be injected in the below cell -
# %%
# -----------------------------------------------------------------------
# %% [markdown]
# ---

# %% [markdown]
# ### Notebook code


# %%
from pynb_dag_runner.tasks.task_opentelemetry_logging import PydarLogger

logger = PydarLogger(P)


# %% [markdown]
# ## Load and limit train data

# %%
def load_and_limit_train_data(P):
    from common.io import datalake_root, read_numpy
    from sklearn.model_selection import train_test_split

    X_train_all = read_numpy(datalake_root(P) / "train-data" / "digits.numpy")
    y_train_all = read_numpy(datalake_root(P) / "train-data" / "labels.numpy")

    assert isinstance(P["task.nr_train_images"], int)

    # Note: train_test_split will fail if split is 0 or 100%.
    assert 0 < P["task.nr_train_images"] < len(y_train_all)

    X_train, _, y_train, _ = train_test_split(
        X_train_all,
        y_train_all,
        train_size=P["task.nr_train_images"],
        test_size=None,
        stratify=y_train_all,
        shuffle=True,
        random_state=123,
    )

    assert X_train.shape == (len(y_train), 8 * 8)
    return X_train, y_train


X_train, y_train = load_and_limit_train_data(P)

# %% [markdown]
# ## Train support vector classifier model
#
# Below we assume that the hyperparameter $C$ is known.
#
# However, this should ideally be found by a hyperparameter search. That could be
# done in parallel on the Ray cluster, but this needs some more work. Ie., to use
# multiple cores in the notebook, those cores should be reserved when starting the
# notebook task (TODO).
#
# - https://docs.ray.io/en/latest/tune/key-concepts.html
#
# Note: cv-scores would need to be computed here, since they depend on the train data.
# After this notebook only the onnx-model is available.

# %%
from sklearn.svm import SVC

# %%
model = SVC(C=10.0, kernel="linear", probability=True)

model.fit(X_train, y_train)

# %% [markdown]
# ### Q: Can the labels returned by `predict(..)` be computed from probabilities returned by the `predict_prob`-method?

# %%
import numpy as np

y_train_labels = model.predict(X_train)
y_train_probabilities = model.predict_proba(X_train)
assert y_train_probabilities.shape == (len(y_train), 10)

y_train_max_prob_labels = np.argmax(y_train_probabilities, axis=1)
assert y_train_labels.shape == y_train_max_prob_labels.shape == y_train.shape

# If the predicted labels would coincide with the labels that have
# maximum probability, the below number would be zero
logger.log_int(
    "nr_max_prob_neq_label", int(sum(y_train_max_prob_labels != y_train_labels))
)

# %% [markdown]
# The explanation is (likely) explained in the SVC source, see
# [here](https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/svm/_base.py).
# Namely, the outputs from `predict(..)` and `predict_proba(..)` may not in some
# cases be compatible since the latter is computed using cross-validation while
# the former is not. Thus, the above number need not be zero.

# %% [markdown]
# ## Persist model

# %%
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

#
from common.io import datalake_root, write_onnx

# %%
# convert sklearn model into onnx and persist to data lake

model_onnx = convert_sklearn(
    model, initial_types=[("float_input_8x8_image", FloatTensorType([None, 8 * 8]))]
)
write_onnx(
    datalake_root(P)
    / "models"
    / f"nr_train_images={P['task.nr_train_images']}"
    / "model.onnx",
    model_onnx,
)

# %%
