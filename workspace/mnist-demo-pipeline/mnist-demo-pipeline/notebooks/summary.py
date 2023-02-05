# %% [markdown]
# # Summarize model performances
#
# This notebooks plots the performances (using averaged ROC AUC scores) for models
# trained with different training sets.

# %% [markdown]
# ### Determine run parameters

# %%
# ----------------- Parameters for interactive development --------------
P = {
    "workflow.run_environment": "dev",
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
#
import pandas as pd
import matplotlib.pyplot as plt

#
from composable_logs.tasks.task_opentelemetry_logging import PydarLogger

# %%
logger = PydarLogger(P=P)

# %%
from composable_logs.tasks.task_opentelemetry_logging import (
    PydarLogger,
    get_logged_values,
)
from composable_logs.opentelemetry_helpers import _get_all_spans, Spans


# %%
def get_model_benchmarks():
    """
    Query the OpenTelemetry logs for *this pipeline run* and return
    all key-values logged from all runs of the benchmark-model.py task

    For testing a json file with OpenTelemetry spans (as an array)
    can be used as follows:

    - Create output directory `mkdir /tmp/spans`
    - Run unit tests. This will create pipeline-outputs/opentelemetry-spans.json
    - Convert this json-array into jsonl format as follows

    jq -c '.[]' /pipeline-outputs/opentelemetry-spans.json > /tmp/spans/data.txt

    """
    spans: Spans = Spans(_get_all_spans())
    print(f" - Found {len(spans)} spans")

    benchmark_spans = (
        spans
        # -
        .filter(["name"], "execute-task")
        # -
        .filter(["attributes", "task.id"], "benchmark-model")
    )

    result = []
    for s in benchmark_spans:
        result.append(
            {
                "span_id": s["context"]["span_id"],
                "nr_train_images": s["attributes"]["task.nr_train_images"],
                "data": get_logged_values(spans.bound_under(s)),
            }
        )

    return result


def adjust_pandas(df):
    def column_renamer(col_name: str) -> str:
        return (
            col_name
            # -- 'data.roc_auc_per_digit.4' -> 'roc_auc.4'
            .replace("data.roc_auc_per_digit", "roc_auc")
            # -- 'data.roc_auc_class_mean' -> 'roc_auc_mean'
            .replace("data.roc_auc_class_mean", "roc_auc_mean")
        )

    return df.rename(column_renamer, axis="columns").sort_values(by="nr_train_images")


# %%

df_data = adjust_pandas(pd.json_normalize(get_model_benchmarks()))

# %%
df_data.round(4)


# %%
def plot_classifier_performance_summary(df_data):
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(16, 4), sharex=True)

    #
    ax.plot(
        df_data["nr_train_images"], df_data["roc_auc_mean"], marker="o", linestyle="--"
    )
    ax.set_title(
        f"ROC AUC digit classifier performance on evaluation digits", fontsize=17
    )
    ax.set_xlabel("Total number of digits in training set", fontsize=14)
    ax.set_ylabel("Mean ROC AUC", fontsize=14)

    fig.tight_layout()
    fig.show()

    return fig


fig = plot_classifier_performance_summary(df_data)

# %%
logger.log_figure("auc-roc-model-performances.png", fig)

# %%
###

# %%
