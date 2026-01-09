import json
from typing import Dict

import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_scan_receive_endpoint(client: TestClient, auth_headers: Dict[str, str]):
    # Minimal payload: itemId + quantity
    payload = {"itemId": "00000000-0000-0000-0000-000000000000", "quantity": 5}
    resp = client.post("/api/v1/inventory/scan/receive", headers=auth_headers, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert isinstance(data["data"], dict)
    # Guidance message exists for directing to purchase orders
    meta = data.get("meta", {})
    # Accept either a guidance field in data or a message in meta depending on implementation
    guidance = data["data"].get("message") or meta.get("message") or data.get("message")
    assert guidance is not None
    assert "purchase" in guidance.lower() or "po" in guidance.lower()


@pytest.mark.asyncio
async def test_scan_pick_endpoint(client: TestClient, auth_headers: Dict[str, str]):
    payload = {"itemId": "00000000-0000-0000-0000-000000000000", "quantity": 2}
    resp = client.post("/api/v1/inventory/scan/pick", headers=auth_headers, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert isinstance(data["data"], dict)
    guidance = data["data"].get("message") or data.get("meta", {}).get("message") or data.get("message")
    assert guidance is not None
    assert "sales" in guidance.lower() or "so" in guidance.lower() or "order" in guidance.lower()


@pytest.mark.asyncio
async def test_scan_count_endpoint(client: TestClient, auth_headers: Dict[str, str]):
    payload = {"itemId": "00000000-0000-0000-0000-000000000000", "quantity": 1}
    resp = client.post("/api/v1/inventory/scan/count", headers=auth_headers, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert isinstance(data["data"], dict)
    guidance = data["data"].get("message") or data.get("meta", {}).get("message") or data.get("message")
    assert guidance is not None
    assert "cycle" in guidance.lower() or "count" in guidance.lower() or "audit" in guidance.lower()
