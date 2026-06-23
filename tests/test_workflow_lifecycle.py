import pytest

import core.workflow as workflow_module


class FakePool:
    def __init__(self, conninfo, *, max_size, open):
        self.conninfo = conninfo
        self.max_size = max_size
        self.open_initially = open
        self.open_calls = []
        self.closed = False

    async def open(self, *, wait=False):
        self.open_calls.append(wait)

    async def close(self):
        self.closed = True


class FakeSaver:
    def __init__(self, pool):
        self.pool = pool


@pytest.mark.asyncio
async def test_workflow_pool_is_ready_before_graph_is_compiled(monkeypatch):
    pool = FakePool(workflow_module.DB_URI, max_size=10, open=False)
    compiled_graph = object()

    monkeypatch.setattr(workflow_module, "AsyncConnectionPool", lambda *args, **kwargs: pool)
    monkeypatch.setattr(workflow_module, "AsyncPostgresSaver", FakeSaver)
    monkeypatch.setattr(workflow_module.workflow, "compile", lambda *, checkpointer: compiled_graph)

    await workflow_module.init_workflow_graph()

    assert pool.open_initially is False
    assert pool.open_calls == [True]
    assert workflow_module.naming_graph is compiled_graph

    await workflow_module.close_workflow_graph()

    assert pool.closed is True
    assert workflow_module.connection_pool is None
    assert workflow_module.naming_graph is None
