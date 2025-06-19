
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_initiate_call():
    response = client.post("/api/notifications/voice", json={"to": "98765", "from_number": "54321"})
    assert response.status_code == 200
    assert response.json()["status"] == "Call initiated"
