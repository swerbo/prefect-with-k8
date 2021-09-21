import pytest

from prefect.executors import DaskExecutor

from prefect_kube_demo.flows.wordcount import mapreduce_wordcount


@pytest.mark.dasktest
def test_mapreduce_wordcount():
    """Distributed wordcount Flow successfully executes using Dask distributed,
    which is deployed on a Kubernetes cluster. The Flow run's state also
    contains correct word count tuples stored in the state's
    associated Result object.
    """

    url = ("https://raw.githubusercontent.com/KTH/ci-hackathon/master/"
           "installations/ci-poetry/supercollider_src/poet10/poem.txt")
    state = mapreduce_wordcount.run(url=url, executor=DaskExecutor())
    task_ref = mapreduce_wordcount.get_tasks("reducer")[0]
    result = state.result[task_ref].result
    # Get top 3 tokens
    result_top_tokens = sorted(result, key=lambda x: x[1])[-3:]
    expected_top_tokens = [("a", 4), ("and", 4), ("the", 5)]
    assert state.is_successful()
    assert result_top_tokens == expected_top_tokens
