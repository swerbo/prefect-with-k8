"""This module contains a MapReduce wordcount program as a Prefect Flow.
This classic MapReduce program was also chosen to demonstrate Prefect's Dask executor.
Note: this module is not meant to be an efficient solution to the word
counting problem. It is only meant to demonstrate distributed workflows in Prefect.
"""

import coiled
import dask
import prefect
import os

from prefect import Flow, Parameter, flatten

from prefect.storage import GitHub
from prefect.run_configs import KubernetesRun, UniversalRun
from prefect.executors import LocalExecutor, DaskExecutor

from prefect_kube_demo.tasks import download_message
from prefect_kube_demo.tasks import split_message
from prefect_kube_demo.tasks import mapper
from prefect_kube_demo.tasks import shuffler
from prefect_kube_demo.tasks import reducer


def get_github_storage():

    # Prefect runs through the entire flow source twice:
    # 1. Upon `prefect register` flows
    # 2. Upon flow run, after the flow's source is downloaded from GitHub

    # Therefore, the following environment variables must be set twice:
    # 1. In the environment from which the flow is registered
    # 2. In the Kubernetes job spun up by the KubernetesAgent to execute flow runs
    # respectively.

    # For 1, these variables can be set as part of the CI/CD pipeline (see GitHub Actions workflows
    # in this repo for an example).
    # For 2, these variables are specified in the custom `job_template.yaml` K8 job config file.

    repo_name = os.environ["REPO_NAME"]
    git_branch = os.environ["GIT_BRANCH"]

    storage = GitHub(
        repo=repo_name,
        ref=git_branch,
        path="src/prefect_kube_demo/flows/wordcount.py",
        # The following secret is specified as an env var in both the
        # Prefect Kubernetes Agent and job configuration files.
        # For Prefect to access this secret, the secret's key must be
        # prefixed by PREFECT__CONTEXT__SECRETS
        access_token_secret="GITHUB_ACCESS_TOKEN",
    )

    return storage


def get_kubernetes_run_config():

    # Agent's are labeled by prod and staging environments.
    # Inspired by Heroku's review apps, the `staging.yaml` workflow
    # creates agents per pull request. With this setup, multiple
    # developers can test their flows on isolated staging environments,
    # which share the same infra as production flow runs.

    is_prod = str(os.environ["IS_PROD"]).lower()
    if is_prod == "false":
        github_pr_id = os.environ["GITHUB_PR_ID"]
        env = f"staging-{github_pr_id}"
    else:
        env = "prod"

    # Agent labels are key value pairs (sep by a colon)
    # This schema is inspired by K8's Labels. Similar to K8 Labels,
    # organising Agent labels in this way allows for
    # efficient queries of Prefect Agents and flow runs.

    agent_type = os.environ["AGENT_TYPE"]
    labels = [f"agent-type:{agent_type}", f"env:{env}"]

    image_name = os.environ["IMAGE_NAME"]
    image_tag = os.environ["IMAGE_TAG"]
    image = f"{image_name}:{image_tag}"

    run_config = KubernetesRun(
        image=image,
        labels=labels,
        job_template_path="agent:/etc/prefect/job_template.yaml",
        # The following image pull secret is stored as a K8 secret
        # in the same namespace as the agent.
        image_pull_secrets=["docker-registry"],
    )

    return run_config


def coiled_cluster():

    # Pass Coiled token from env vars specified in `job_template.yaml` and
    # stored in K8 secrets in the same namespace as the agent.
    coiled_token = os.environ["COILED_TOKEN"]

    # IMPORTANT! As of Prefect v0.15.5, Prefect context values passed to the flow run are loaded
    # AFTER the flow source has been downloaded and run through once (before
    # the start of task runs). Therefore, variables passed to the context
    # via the `--context` flag with the CLI command `prefect run` will NOT
    # show up within `get_kubernetes_run_config` and `get_github_storage`

    # Nevertheless, because DaskExecutor creates the Dask cluster AFTER
    # the flow source is run through, therefore Prefect contexts can be
    # used to dynamically change Coiled software environments and
    # cluster configurations (e.g. n_workers, worker_cpu, scheduler_cpu)

    try:
        coiled_software_env = prefect.context.COILED_SOFTWARE_ENV
    except AttributeError:
        coiled_software_env = os.environ["DEFAULT_COILED_SOFTWARE"]
    
    try:
        coiled_cluster_config = prefect.context.COILED_CLUSTER_CONFIG
    except AttributeError:
        coiled_cluster_config = os.environ["DEFAULT_COILED_CLUSTER_CONFIG"]

    # Authenticate to Coiled Cloud
    dask.config.set({"coiled.token": coiled_token})

    return coiled.Cluster(
        software=coiled_software_env, configuration=coiled_cluster_config
    )


def get_executor():

    if os.environ["USE_LOCAL_EXECUTOR"]:
        executor = LocalExecutor()

    else:
        if os.environ.get("USE_COILED"):
            executor = DaskExecutor(
                cluster_class=coiled_cluster,
            )
        else:
            executor = DaskExecutor()

    return executor


with Flow(
    name="mapreduce-wordcount",
    storage=get_github_storage(),
    run_config=get_kubernetes_run_config(),
    executor=get_executor(),
) as mapreduce_wordcount:

    url = Parameter("url", required=True)

    message = download_message(url)
    lines = split_message(message)
    token_tuples = mapper.map(lines)
    partitions = shuffler(flatten(token_tuples))
    token_counts = reducer.map(partitions)


if __name__ == "__main__":

    # Local flow run: only used for preliminary testing

    # As discussed in the README.md, I believe it is best practice
    # that the dev environment is as close as possible to staging and production.

    # This means that flow runs should be executed using Prefect backend
    # and your local Kubernetes cluster (e.g. minikube) in development ASAP.

    mapreduce_wordcount.run(
        parmeters={
            "url": "https://raw.githubusercontent.com/topher-lo/prefect-with-k8/main/src/prefect_kube_demo/data/dream.txt"
        },
        executor=DaskExecutor(),
    )
