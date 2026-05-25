# tests/test_exhaustive.py
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.utils.store import store

client = TestClient(app)
API_VERSION = "2024-05-25"
OLD_API_VERSION = "2024-05-01"
INVALID_API_VERSION = "2000-01-01"

@pytest.fixture(autouse=True)
def reset_store():
    """Clear and re-seed store before each test."""
    store.notes.clear()
    store.seed()

# --- API VERSIONING TESTS ---

def test_missing_api_version():
    """Test that missing api-version returns 400 with structured error."""
    response = client.get("/health") # No api-version
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "MissingApiVersion"
    assert "required" in data["error"]["message"]
    assert "availableVersions" in data["error"]

def test_invalid_api_version():
    """Test that invalid api-version returns 400 with structured error."""
    response = client.get(f"/health?api-version={INVALID_API_VERSION}")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "UnsupportedApiVersion"
    assert INVALID_API_VERSION in data["error"]["message"]

def test_supported_api_versions():
    """Test all supported api-versions."""
    for version in [API_VERSION, OLD_API_VERSION]:
        response = client.get(f"/health?api-version={version}")
        assert response.status_code == 200

# --- HEALTH CHECK TESTS ---

def test_health_check_complete():
    response = client.get(f"/health?api-version={API_VERSION}")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# --- LIST NOTES (GET /notes) TESTS ---

def test_list_notes_no_params():
    response = client.get(f"/notes?api-version={API_VERSION}")
    assert response.status_code == 200
    data = response.json()
    assert "value" in data
    assert len(data["value"]) == 3 # Default seeded count

def test_list_notes_limit_alias():
    """Test 'limit' as alias for 'top' (Bonus Challenge)."""
    response = client.get(f"/notes?api-version={API_VERSION}&limit=1")
    assert response.status_code == 200
    assert len(response.json()["value"]) == 1

def test_list_notes_page_alias():
    """Test 'page' and 'limit' (Bonus Challenge)."""
    # 3 notes: [0, 1, 2]. Limit 1, Page 2 should give note index 1.
    all_notes = client.get(f"/notes?api-version={API_VERSION}&orderby=createdAt asc").json()["value"]
    response = client.get(f"/notes?api-version={API_VERSION}&limit=1&page=2&orderby=createdAt asc")
    assert response.status_code == 200
    data = response.json()
    assert len(data["value"]) == 1
    assert data["value"][0]["id"] == all_notes[1]["id"]

def test_list_notes_orderby_asc_desc():
    """Test sorting logic."""
    # Descending
    response = client.get(f"/notes?api-version={API_VERSION}&orderby=title desc")
    titles_desc = [n["title"] for n in response.json()["value"]]
    assert titles_desc == sorted(titles_desc, reverse=True)
    
    # Ascending
    response = client.get(f"/notes?api-version={API_VERSION}&orderby=title asc")
    titles_asc = [n["title"] for n in response.json()["value"]]
    assert titles_asc == sorted(titles_asc)

def test_list_notes_filter_complex():
    """Test filtering with different quotes and casing."""
    # Quoted
    r1 = client.get(f"/notes?api-version={API_VERSION}&filter=tag eq 'work'")
    # Unquoted (Bonus handling)
    r2 = client.get(f"/notes?api-version={API_VERSION}&filter=tag eq work")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert len(r1.json()["value"]) == len(r2.json()["value"])

# --- CREATE NOTE (POST /notes) TESTS ---

def test_create_note_exhaustive_validation():
    """Test various validation failures for POST."""
    # Body too short
    payload = {"title": "Valid Title", "body": "a"}
    response = client.post(f"/notes?api-version={API_VERSION}", json=payload)
    assert response.status_code == 400
    assert response.json()["error"]["details"][0]["target"] == "body"

    # Title too long
    payload = {"title": "a" * 151, "body": "Valid body content"}
    response = client.post(f"/notes?api-version={API_VERSION}", json=payload)
    assert response.status_code == 400
    
    # Missing required field
    payload = {"title": "Missing Body"}
    response = client.post(f"/notes?api-version={API_VERSION}", json=payload)
    assert response.status_code == 400

# --- BULK CREATE (POST /notes/bulk) TESTS ---

def test_bulk_create_large_payload():
    payload = [{"title": f"Note {i}", "body": f"Body for note {i}"} for i in range(10)]
    response = client.post(f"/notes/bulk?api-version={API_VERSION}", json=payload)
    assert response.status_code == 201
    assert len(response.json()["value"]) == 10

# --- GET SINGLE NOTE (GET /notes/{id}) TESTS ---

def test_get_note_by_id_formats():
    all_notes = client.get(f"/notes?api-version={API_VERSION}").json()["value"]
    note_id = all_notes[0]["id"]
    
    # Valid
    response = client.get(f"/notes/{note_id}?api-version={API_VERSION}")
    assert response.status_code == 200
    
    # Not Found
    response = client.get(f"/notes/00000000-0000-0000-0000-000000000000?api-version={API_VERSION}")
    assert response.status_code == 404

# --- REPLACE NOTE (PUT /notes/{id}) TESTS ---

def test_put_full_replace():
    all_notes = client.get(f"/notes?api-version={API_VERSION}").json()["value"]
    note_id = all_notes[0]["id"]
    
    # Missing field (PUT requires full object)
    payload = {"title": "Only Title"}
    response = client.put(f"/notes/{note_id}?api-version={API_VERSION}", json=payload)
    assert response.status_code == 400
    
    # Valid Full Replace
    payload = {"title": "Full Replace", "body": "Entirely new body content."}
    response = client.put(f"/notes/{note_id}?api-version={API_VERSION}", json=payload)
    assert response.status_code == 200
    assert response.json()["title"] == "Full Replace"
    assert response.json()["body"] == "Entirely new body content."
    assert response.json()["tags"] == [] # Default empty list

# --- PARTIAL UPDATE (PATCH /notes/{id}) TESTS ---

def test_patch_idempotency_behavior():
    all_notes = client.get(f"/notes?api-version={API_VERSION}").json()["value"]
    note_id = all_notes[0]["id"]
    
    payload = {"title": "Constant Title"}
    # Call 1
    r1 = client.patch(f"/notes/{note_id}?api-version={API_VERSION}", json=payload)
    # Call 2
    r2 = client.patch(f"/notes/{note_id}?api-version={API_VERSION}", json=payload)
    
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["title"] == r2.json()["title"]
    assert r1.json()["updatedAt"] != r2.json()["updatedAt"] # Timestamp should update

# --- DELETE NOTE (DELETE /notes/{id}) TESTS ---

def test_delete_and_verify_cleanup():
    all_notes = client.get(f"/notes?api-version={API_VERSION}").json()["value"]
    original_count = len(all_notes)
    note_id = all_notes[0]["id"]
    
    # Delete
    response = client.delete(f"/notes/{note_id}?api-version={API_VERSION}")
    assert response.status_code == 200
    
    # Verify count decreased
    response = client.get(f"/notes?api-version={API_VERSION}")
    assert len(response.json()["value"]) == original_count - 1

# --- ERROR RESPONSE SHAPE TESTS ---

def test_error_envelope_consistency():
    """Ensure all errors follow Azure standard { error: { code, message } }."""
    # 404
    r404 = client.get(f"/notes/missing-id?api-version={API_VERSION}")
    # 400 (Validation)
    r400v = client.post(f"/notes?api-version={API_VERSION}", json={"title": "t"}) # No body
    # 400 (Version)
    r400ver = client.get("/notes") # No version
    
    for r in [r404, r400v, r400ver]:
        data = r.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
