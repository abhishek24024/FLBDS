from fastapi.testclient import TestClient
from flbds.api.server import app

client = TestClient(app)

def test_api_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "3.0.0"

def test_api_thesaurus_endpoints():
    resp = client.get("/api/thesaurus/graphs")
    assert resp.status_code == 200
    graphs = resp.json()
    assert len(graphs) >= 10

    resp_search = client.get("/api/thesaurus/search?q=shark+drag+reduction")
    assert resp_search.status_code == 200
    assert len(resp_search.json()) > 0

def test_api_pipeline_run():
    resp = client.post("/api/pipeline/run?case=lotus")
    assert resp.status_code == 200
    data = resp.json()
    assert data["case"] == "lotus"
    assert "alignment" in data
    assert "scaling_audit" in data
    assert "triz_resolution" in data
    assert "synthesis" in data
    assert data["synthesis"]["keep_out_drift_mse"] == 0.0
    assert "<svg" in data["synthesis"]["svg_schematic"]

def test_api_index_page():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "FLBDS v3.0" in resp.text
