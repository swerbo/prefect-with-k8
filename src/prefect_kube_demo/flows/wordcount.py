"""This module contains a MapReduce wordcount program as a Prefect Flow.
This classic MapReduce program was also chosen to demonstrate Prefect's Dask executor.
Note: this module is not meant to be an efficient solution to the word
counting problem. It is only meant to demonstrate distributed workflows in Prefect.
"""

from prefect import Flow, Parameter, flatten

from prefect.storage import GitHub
from prefect.run_configs import KubernetesRun
from prefect.executors import DaskExecutor

from prefect_kube_demo.tasks import download_message
from prefect_kube_demo.tasks import split_message
from prefect_kube_demo.tasks import mapper
from prefect_kube_demo.tasks import shuffler
from prefect_kube_demo.tasks import reducer


with Flow(name="mapreduce-wordcount") as mapreduce_wordcount:

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
        parmeters={"url": "https://raw.githubusercontent.com/topher-lo/prefect-with-k8/main/src/prefect_kube_demo/data/dream.txt"},
        executor=DaskExecutor()
    )
