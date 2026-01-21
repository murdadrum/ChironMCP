from starlette.testclient import TestClient

from chiron_mcp_server.server import create_app


def test_health_endpoint():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True


def test_ui_diagram_endpoint():
    client = TestClient(create_app())
    spec = {
        "type": "ui_diagram",
        "editor": "PROPERTIES",
        "tab": "MODIFIERS",
        "callout": "Click Add Modifier",
        "breadcrumbs": ["Properties", "Modifiers", "Add Modifier"],
    }
    response = client.post("/ui/diagram", json=spec)
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["image_base64"]
