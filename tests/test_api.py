from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_extract_requires_image_upload():
    response = client.post("/extract", files={"file": ("test.txt", b"hello", "text/plain")})

    assert response.status_code == 400
    assert response.json()["detail"] == "Please upload a valid image file"
