"""Packaging boot smoke (CI: container-smoke job).

Runs inside a clean python:3.11-slim container where openkb was installed
from the built wheel with all extras. Boots the REST app with no LLM
calls. Catches broken wheels, missing deps, missing extras (#46 class)
and API import/boot regressions.
"""

from fastapi.testclient import TestClient

from openkb.api import create_app

client = TestClient(create_app())
resp = client.get("/")
assert resp.status_code < 500, f"GET / -> {resp.status_code}"
print("boot smoke ok:", resp.status_code)
