
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_send_sms():
    response = client.post("/api/notifications/sms", json={"to": "12345", "message": "Hi"})
    assert response.status_code == 200
    assert response.json()["status"] == "SMS sent"
