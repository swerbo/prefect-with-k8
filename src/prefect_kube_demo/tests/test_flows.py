from prefect.executors import DaskExecutor

from prefect_kube_demo.flows.wordcount import mapreduce_wordcount


def test_mapreduce_wordcount():
    """Distributed wordcount Flow successfully executes using a Local Dask cluster.
    The Flow run's state returns word count tuples stored in the state's
    associated Result object.
    """

    state = mapreduce_wordcount.run(
        url="https://raw.githubusercontent.com/topher-lo/prefect-with-k8/main/src/prefect_kube_demo/data/dream.txt",
        executor=DaskExecutor()
    )
    task_ref = mapreduce_wordcount.get_tasks("reducer")[0]
    result = state.result[task_ref].result
    # Get top 3 tokens
    result_top_tokens = sorted(result, key=lambda x: x[1])[-3:]
    expected_top_tokens = [("will", 17), ("freedom", 13), ("from", 12)]
    assert state.is_successful()
    assert result_top_tokens == expected_top_tokens
