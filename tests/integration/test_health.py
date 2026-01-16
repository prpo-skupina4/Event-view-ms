# tests/integration/test_health.py
import pytest

@pytest.mark.anyio
async def test_health_ok(client):
    r = await client.get("/urniki/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
