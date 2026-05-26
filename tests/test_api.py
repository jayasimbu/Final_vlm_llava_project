from fastapi.testclient import TestClient
import pytest
import os

from app.main import app

client = TestClient(app)


def test_extract_requires_image_upload():
    response = client.post("/extract", files={"file": ("test.txt", b"hello", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Please upload a valid image file"


def test_extract_and_ask_wert_jpg():
    # Verify wert.jpg exists
    assert os.path.exists("wert.jpg"), "wert.jpg sample invoice is missing from project root!"

    # 1. Test extraction endpoint
    with open("wert.jpg", "rb") as f:
        response = client.post(
            "/extract",
            files={"file": ("wert.jpg", f, "image/jpeg")}
        )
    
    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json["status"] == "success"
    
    data = resp_json["data"]
    assert data["vendor_name"] == "Raga Pvt Ltd"
    assert data["invoice_number"] == "SR2"
    assert data["invoice_date"] == "2020-03-23"
    assert data["invoice_time"] == "04:57 PM"
    assert data["subtotal"] == 760.0
    assert data["discount"] == 26.0
    assert data["tax"] == 77.0
    assert data["total_amount"] == 811.0
    
    items = data["items"]
    assert len(items) == 2
    assert items[0]["name"] == "Alternagel"
    assert items[0]["qty"] == "1"
    assert items[0]["price"] == 200.0
    assert items[1]["name"] == "Bepanthen"
    assert items[1]["qty"] == "1"
    assert items[1]["price"] == 560.0

    # 2. Test QA endpoint (/ask)
    # Question: Date
    qa_resp = client.post("/ask", json={
        "question": "what is the invoice date?",
        "invoice_data": data
    })
    assert qa_resp.status_code == 200
    assert qa_resp.json()["answer"] == "2020-03-23"

    # Question: GST/Tax
    qa_resp = client.post("/ask", json={
        "question": "what is the GST amount?",
        "invoice_data": data
    })
    assert qa_resp.status_code == 200
    assert qa_resp.json()["answer"] == "77.0"

    # Question: Time
    qa_resp = client.post("/ask", json={
        "question": "at what time was this invoice issued?",
        "invoice_data": data
    })
    assert qa_resp.status_code == 200
    assert qa_resp.json()["answer"] == "04:57 PM"

    # Question: Vendor
    qa_resp = client.post("/ask", json={
        "question": "who is the vendor?",
        "invoice_data": data
    })
    assert qa_resp.status_code == 200
    assert qa_resp.json()["answer"] == "Raga Pvt Ltd"

    # Question: Total Amount
    qa_resp = client.post("/ask", json={
        "question": "what is the total amount?",
        "invoice_data": data
    })
    assert qa_resp.status_code == 200
    assert qa_resp.json()["answer"] == "811.0"

