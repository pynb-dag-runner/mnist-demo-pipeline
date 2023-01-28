# %% [markdown]
# # Benchmark model
#
# The purpose of this notebook is to benchmark persisted onnx-model (trained in the
# previous step) against evaluation set.

# %% [markdown]
# ### Determine run parameters

# %%
# ----------------- Parameters for interactive development --------------
P = {
    "workflow.data_lake_root": "/pipeline-outputs/data-lake",
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
import itertools as it

#
import numpy as np
import matplotlib.pyplot as plt

#
from pynb_dag_runner.tasks.task_opentelemetry_logging import PydarLogger

#
from common.io import datalake_root

logger = PydarLogger(P)

# %% [markdown]
# ## Load persisted onnx-model and evaluation data

# %%
from common.io import read_onnx, get_onnx_inputs, get_onnx_outputs, read_numpy

# %%
onnx_inference_session = read_onnx(
    datalake_root(P)
    / "models"
    / f"nr_train_images={P['task.nr_train_images']}"
    / "model.onnx"
)
# %% [markdown]
# ### Record structure of inputs and outputs for ONNX model
#
# (this should likely be done in training notebook)

# %%
import json

onnx_io = json.dumps(
    {
        "inputs": get_onnx_inputs(onnx_inference_session),
        "outputs": get_onnx_outputs(onnx_inference_session),
    },
    indent=2,
)


logger.log_artefact("onnx_io_structure.json", onnx_io)
print(onnx_io)

# %% [markdown]
# ### Evaluate model performance on evaluation data set

# %%
# load evaluation data
X_test = read_numpy(datalake_root(P) / "test-data" / "digits.numpy")
y_test = read_numpy(datalake_root(P) / "test-data" / "labels.numpy")


# %%
def get_model_outputs(X, onnx_inference_session):
    y_pred_labels, y_pred_map = onnx_inference_session.run(
        ["output_label", "output_probability"],
        {"float_input_8x8_image": X.astype(np.float32)},
    )
    y_pred_probs = np.array(
        [[probabilities[digit] for digit in range(10)] for probabilities in y_pred_map]
    )

    assert y_pred_labels.shape == (X.shape[0],)
    assert y_pred_probs.shape == (X.shape[0], 10)

    return y_pred_labels, y_pred_probs


# Note: as shown in the training notebook, the predicted labels and probabilities
# computed below need not be compatible.
y_pred_labels_test, y_pred_probs_test = get_model_outputs(
    X_test, onnx_inference_session
)


# %% [markdown]
# ### Confusion matrix

# %%
# TODO

# %% [markdown]
# ### Plot predicted probabilities for each classifier over all evaluation digit images

# %%
def plot_per_digit_probabilities(y_pred_probs):
    fig, axs = plt.subplots(nrows=2, ncols=5, figsize=(16, 6))

    for (r, c), digit, ax in zip(
        it.product(range(2), range(5)), range(10), axs.reshape(-1)
    ):
        ax.hist(y_pred_probs_test[:, digit], bins=20)

        ax.set_title(f"Digit {digit}")
        if r == 1 and c == 2:
            ax.set_xlabel("probability", fontsize=16)

        if c == 0:
            ax.set_ylabel("counts", fontsize=16)
        ax.set_yscale("log")

    fig.tight_layout()
    fig.suptitle(
        f"Distributions of prediction probabilities for each digit "
        f"(on evaluation data, n={y_pred_probs.shape[0]})",
        fontsize=20,
    )
    fig.tight_layout()
    fig.show()

    return fig


fig = plot_per_digit_probabilities(y_pred_probs_test)

# %% [markdown]
# From the above distributions we see that most digits have clear separation between
# high and lower probabilities. Morover, in each case there is roughly an order of
# magnitude more of digits with low probabilities. This is compatible with digits
# being roughly evenly distributed in the data.

# %%
logger.log_figure("per-digit-probabilities.png", fig)

# %% [markdown]
# ### Plot ROC curves for individual one-vs-rest classifiers

# %%
from sklearn import metrics


# %%
def plot_roc_curves(y, y_pred_probs):
    # based on example code
    # https://scikit-learn.org/stable/auto_examples/model_selection/plot_roc.html

    fig, axs = plt.subplots(nrows=2, ncols=5, figsize=(16, 8))

    roc_auc_dict = {}

    for (r, c), digit, ax in zip(
        it.product(range(2), range(5)), range(10), axs.reshape(-1)
    ):
        fpr, tpr, _ = metrics.roc_curve(y == digit, y_pred_probs[:, digit])
        auc = metrics.auc(fpr, tpr)
        roc_auc_dict[str(digit)] = auc

        ax.plot(fpr, tpr, label=f"ROC AUC={round(auc, 3)}")

        ax.set_title(f"\nDigit {digit}", fontsize=16)
        if r == 1:
            ax.set_xlabel("FPR", fontsize=18)

        if c == 0:
            ax.set_ylabel("TPR", fontsize=18)

        ax.set_xlim([-0.05, 1.05])
        ax.set_ylim([-0.05, 1.05])
        ax.legend(loc="lower right", frameon=False, fontsize=14)

    fig.tight_layout()
    fig.suptitle(
        f"ROC plots for one-vs-rest performances "
        f"(on evaluation data, n={y_pred_probs_test.shape[1]}",
        fontsize=22,
    )
    fig.tight_layout()
    fig.show()

    return roc_auc_dict, fig


roc_auc_dict, fig = plot_roc_curves(y_test, y_pred_probs_test)

# %%
logger.log_figure("per-digit-roc-curves.png", fig)

# %%
roc_auc_dict

# %%
logger.log_value("roc_auc_per_digit", roc_auc_dict)

# %% [markdown]
# ### Compute and log mean ROC AUC score averaged over all digits

# %%
roc_auc_macro = np.mean(list(roc_auc_dict.values()))

logger.log_float("roc_auc_class_mean", roc_auc_macro)

# assert that the same value can be computed directly using sklearn
assert roc_auc_macro == metrics.roc_auc_score(
    y_test, y_pred_probs_test, average="macro", multi_class="ovr"
)

# %%
# ---
# %%
