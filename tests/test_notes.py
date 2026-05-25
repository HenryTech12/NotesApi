# tests/test_notes.py
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.utils.store import store

client = TestClient(app)
API_VERSION = "2024-05-25"

@pytest.fixture(autouse=True)
def reset_store():
    # Clear and re-seed store before each test for isolation
    store.notes.clear()
    store.seed()

def test_health_check():
    response = client.get(f"/health?api-version={API_VERSION}")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_note_success():
    payload = {
        "title": "Test Note",
        "body": "This is a test body content.",
        "tags": ["test", "pytest"]
    }
    response = client.post(f"/notes?api-version={API_VERSION}", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Note"
    assert "id" in data

def test_create_note_validation_error():
    # Title too short/empty
    payload = {"title": "", "body": "Too short"}
    response = client.post(f"/notes?api-version={API_VERSION}", json=payload)
    assert response.status_code == 400
    assert "error" in response.json()
    assert response.json()["error"]["code"] == "InvalidRequest"

def test_list_notes_pagination():
    # Store seeded with 3 notes
    response = client.get(f"/notes?api-version={API_VERSION}&top=2&skip=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["value"]) == 2
    assert "nextLink" in data
    assert data["nextLink"] is not None

def test_list_notes_filter_tag():
    # Filter using Azure pattern: tag eq 'val'
    response = client.get(f"/notes?api-version={API_VERSION}&filter=tag eq 'fastapi'")
    assert response.status_code == 200
    data = response.json()
    assert len(data["value"]) >= 1
    assert any("fastapi" in note["tags"] for note in data["value"])

def test_list_notes_search():
    response = client.get(f"/notes?api-version={API_VERSION}&search=Strategy")
    assert response.status_code == 200
    data = response.json()
    assert len(data["value"]) == 1
    assert "Strategy" in data["value"][0]["title"]

def test_get_single_note_success():
    # Get first seeded note
    all_notes = client.get(f"/notes?api-version={API_VERSION}").json()["value"]
    note_id = all_notes[0]["id"]
    
    response = client.get(f"/notes/{note_id}?api-version={API_VERSION}")
    assert response.status_code == 200
    assert response.json()["id"] == note_id

def test_get_single_note_not_found():
    response = client.get(f"/notes/non-existent-id?api-version={API_VERSION}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ResourceNotFound"

def test_put_replace_note():
    all_notes = client.get(f"/notes?api-version={API_VERSION}").json()["value"]
    note_id = all_notes[0]["id"]
    
    payload = {
        "title": "Explosive Update",
        "body": "New body content here.",
        "tags": ["updated"]
    }
    response = client.put(f"/notes/{note_id}?api-version={API_VERSION}", json=payload)
    assert response.status_code == 200
    assert response.json()["title"] == "Explosive Update"

def test_patch_partial_update():
    all_notes = client.get(f"/notes?api-version={API_VERSION}").json()["value"]
    note_id = all_notes[0]["id"]
    original_body = all_notes[0]["body"]
    
    payload = {"title": "Only Title Updated"}
    response = client.patch(f"/notes/{note_id}?api-version={API_VERSION}", json=payload)
    assert response.status_code == 200
    assert response.json()["title"] == "Only Title Updated"
    assert response.json()["body"] == original_body

def test_create_notes_bulk_success():
    payload = [
        {"title": "Bulk 1", "body": "Body 1", "tags": ["bulk"]},
        {"title": "Bulk 2", "body": "Body 2"}
    ]
    
    response = client.post(f"/notes/bulk?api-version={API_VERSION}", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert len(data["value"]) == 2
    assert data["value"][0]["title"] == "Bulk 1"
    assert data["value"][1]["title"] == "Bulk 2"

def test_patch_validation_empty_payload():
    all_notes = client.get(f"/notes?api-version={API_VERSION}").json()["value"]
    note_id = all_notes[0]["id"]
    
    response = client.patch(f"/notes/{note_id}?api-version={API_VERSION}", json={})
    assert response.status_code == 400
    assert "at least one" in response.json()["error"]["details"][0]["message"].lower()

def test_delete_note():
    all_notes = client.get(f"/notes?api-version={API_VERSION}").json()["value"]
    note_id = all_notes[0]["id"]
    
    response = client.delete(f"/notes/{note_id}?api-version={API_VERSION}")
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = client.get(f"/notes/{note_id}?api-version={API_VERSION}")
    assert get_response.status_code == 404

def test_delete_note_idempotency():
    response = client.delete(f"/notes/already-deleted?api-version={API_VERSION}")
    # Microsoft Guideline 7.5: DELETE should return 204 even if resource is missing
    assert response.status_code == 204
