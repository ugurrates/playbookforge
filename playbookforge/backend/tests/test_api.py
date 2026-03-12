"""Tests for FastAPI endpoints."""

import json

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ── Health & Info ────────────────────────────────────────────────────

class TestHealthEndpoints:
    def test_root(self, client: TestClient):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "PlaybookForge API"
        assert data["version"] == "0.1.0"

    def test_health(self, client: TestClient):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_platforms(self, client: TestClient):
        r = client.get("/platforms")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 6
        ids = {p["platform_id"] for p in data["platforms"]}
        assert "xsoar" in ids
        assert "shuffle" in ids
        assert "sentinel" in ids
        assert "fortisoar" in ids
        assert "splunk_soar" in ids
        assert "google_secops" in ids


# ── Validation ───────────────────────────────────────────────────────

class TestValidateEndpoint:
    def test_validate_valid_playbook(self, client: TestClient, sample_playbook_dict: dict):
        r = client.post("/validate", json={"playbook": sample_playbook_dict})
        assert r.status_code == 200
        data = r.json()
        assert data["valid"] is True
        assert data["error_count"] == 0

    def test_validate_invalid_playbook(self, client: TestClient):
        r = client.post("/validate", json={"playbook": {"name": "bad"}})
        assert r.status_code == 200
        data = r.json()
        assert data["valid"] is False
        assert data["error_count"] >= 1


# ── Conversion ───────────────────────────────────────────────────────

class TestConvertEndpoint:
    @pytest.mark.parametrize("platform", ["xsoar", "shuffle", "sentinel", "fortisoar"])
    def test_convert_to_platform(self, client: TestClient, sample_playbook_dict: dict, platform: str):
        r = client.post("/convert", json={
            "playbook": sample_playbook_dict,
            "target_platform": platform,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["platform"] == platform
        assert len(data["content"]) > 0
        assert len(data["filename"]) > 0

    def test_convert_invalid_platform(self, client: TestClient, sample_playbook_dict: dict):
        r = client.post("/convert", json={
            "playbook": sample_playbook_dict,
            "target_platform": "nonexistent",
        })
        assert r.status_code == 400

    def test_convert_invalid_playbook(self, client: TestClient):
        r = client.post("/convert", json={
            "playbook": {"bad": "data"},
            "target_platform": "xsoar",
        })
        assert r.status_code == 400


class TestConvertAllEndpoint:
    def test_convert_all(self, client: TestClient, sample_playbook_dict: dict):
        r = client.post("/convert/all", json={"playbook": sample_playbook_dict})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert len(data["results"]) == 6
        for pid, result in data["results"].items():
            assert result["success"] is True

    def test_convert_all_invalid_playbook(self, client: TestClient):
        r = client.post("/convert/all", json={"playbook": {"bad": "data"}})
        assert r.status_code == 400


class TestDownloadEndpoint:
    def test_download_xsoar(self, client: TestClient, sample_playbook_dict: dict):
        r = client.post("/convert/download/xsoar", json={"playbook": sample_playbook_dict})
        assert r.status_code == 200
        assert "content-disposition" in r.headers
        assert ".yml" in r.headers["content-disposition"]

    def test_download_invalid_platform(self, client: TestClient, sample_playbook_dict: dict):
        r = client.post("/convert/download/nonexistent", json={"playbook": sample_playbook_dict})
        assert r.status_code == 400


# ── Playbook Summary ────────────────────────────────────────────────

class TestSummaryEndpoint:
    def test_summary(self, client: TestClient, sample_playbook_dict: dict):
        r = client.post("/playbook/summary", json={"playbook": sample_playbook_dict})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Phishing Email Investigation & Response"
        assert data["total_steps"] == 12
        assert data["action_steps"] > 0

    def test_summary_invalid(self, client: TestClient):
        r = client.post("/playbook/summary", json={"playbook": {"bad": "data"}})
        assert r.status_code == 400
