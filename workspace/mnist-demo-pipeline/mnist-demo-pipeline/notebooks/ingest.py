# %% [markdown]
# # Ingest toy version of MNIST digit data from sklearn

# %% [markdown]
# ### Determine run parameters

# %%
# ----------------- Parameters for interactive development --------------
P = {
    "workflow.run_environment": "dev",
    "workflow.data_lake_root": "/pipeline-outputs/data-lake",
    "run.retry_nr": "1",
}
# %% tags=["parameters"]
# - During automated runs parameters will be injected in the below cell -
# %%
# -----------------------------------------------------------------------
# %% [markdown]
# ---


# %% [markdown]
# ### Simulate different types of failures (for testing timeout and retry logic)

# %%
from pynb_dag_runner.tasks.task_opentelemetry_logging import PydarLogger

logger = PydarLogger(P)

# %% [markdown]
# ### Notebook code


# %%
from sklearn import datasets

#
from common.io import datalake_root, write_numpy

# %%
digits = datasets.load_digits()

X = digits["data"]
y = digits["target"]


# %%
logger.log_value("data_shape", list(X.shape))
logger.log_value("target_shape", list(y.shape))

X.shape, y.shape

# %%
write_numpy(datalake_root(P) / "raw" / "digits.numpy", X)
write_numpy(datalake_root(P) / "raw" / "labels.numpy", y)

# %%
