# tests/test_notes.py
# Exhaustive test suite — every endpoint, every status code, every edge case.
# Run with: PYTHONPATH=$PWD pytest tests/test_notes.py -v

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.utils.store import store

client = TestClient(app)
API_VERSION = "2024-05-25"
OLD_API_VERSION = "2024-05-01"
BAD_API_VERSION = "1999-01-01"
BASE = f"?api-version={API_VERSION}"


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_store():
    """Wipe and re-seed the store before every single test for full isolation."""
    store.notes.clear()
    store.seed()


@pytest.fixture
def seeded_ids():
    """Return the IDs of the 3 seeded notes in insertion order."""
    return list(store.notes.keys())


@pytest.fixture
def first_id(seeded_ids):
    return seeded_ids[0]


def make_note(title="My Note", body="This is a valid body.", tags=None):
    """Helper to POST a fresh note and return the response JSON."""
    payload = {"title": title, "body": body}
    if tags is not None:
        payload["tags"] = tags
    r = client.post(f"/notes{BASE}", json=payload)
    assert r.status_code == 201, f"make_note failed: {r.json()}"
    return r.json()


# ─────────────────────────────────────────────────────────────────────────────
# 1. API VERSIONING
# ─────────────────────────────────────────────────────────────────────────────

class TestApiVersioning:

    def test_missing_api_version_returns_400(self):
        # Implementation has been updated to require api-version
        r = client.get("/notes")
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "MissingApiVersion"

    def test_valid_current_version_accepted(self):
        r = client.get(f"/notes?api-version={API_VERSION}")
        assert r.status_code == 200

    def test_valid_old_version_accepted(self):
        r = client.get(f"/notes?api-version={OLD_API_VERSION}")
        assert r.status_code == 200

    def test_unsupported_version_returns_400(self):
        r = client.get(f"/notes?api-version={BAD_API_VERSION}")
        assert r.status_code == 400

    def test_unsupported_version_error_shape(self):
        r = client.get(f"/notes?api-version={BAD_API_VERSION}")
        body = r.json()
        assert "error" in body
        assert "message" in body["error"]

    def test_unsupported_version_on_post(self):
        r = client.post(
            f"/notes?api-version={BAD_API_VERSION}",
            json={"title": "T", "body": "Body here"}
        )
        assert r.status_code == 400

    def test_unsupported_version_on_get_single(self):
        r = client.get(f"/notes/some-id?api-version={BAD_API_VERSION}")
        assert r.status_code == 400

    def test_unsupported_version_on_delete(self):
        r = client.delete(f"/notes/some-id?api-version={BAD_API_VERSION}")
        assert r.status_code == 400

    def test_api_version_on_health_endpoint(self):
        r = client.get(f"/health?api-version={API_VERSION}")
        assert r.status_code == 200

    def test_unsupported_version_on_health(self):
        r = client.get(f"/health?api-version={BAD_API_VERSION}")
        assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# 2. HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthCheck:

    def test_health_returns_200(self):
        r = client.get(f"/health{BASE}")
        assert r.status_code == 200

    def test_health_response_body(self):
        r = client.get(f"/health{BASE}")
        assert r.json() == {"status": "ok"}

    def test_health_content_type_is_json(self):
        r = client.get(f"/health{BASE}")
        assert "application/json" in r.headers["content-type"]

    def test_health_with_valid_api_version(self):
        r = client.get(f"/health?api-version={API_VERSION}")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ─────────────────────────────────────────────────────────────────────────────
# 3. POST /notes — CREATE
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateNote:

    # ── Success ───────────────────────────────────────────────────────────────

    def test_create_returns_201(self):
        r = client.post(f"/notes{BASE}", json={"title": "Hello", "body": "World body here"})
        assert r.status_code == 201

    def test_create_returns_note_with_id(self):
        r = client.post(f"/notes{BASE}", json={"title": "Hello", "body": "World body here"})
        data = r.json()
        assert "id" in data
        assert isinstance(data["id"], str)
        assert len(data["id"]) > 0

    def test_create_returns_correct_title_and_body(self):
        r = client.post(f"/notes{BASE}", json={"title": "My Title", "body": "My body text here"})
        data = r.json()
        assert data["title"] == "My Title"
        assert data["body"] == "My body text here"

    def test_create_with_tags(self):
        r = client.post(f"/notes{BASE}", json={"title": "Tagged", "body": "Body content here", "tags": ["a", "b"]})
        assert r.status_code == 201
        assert r.json()["tags"] == ["a", "b"]

    def test_create_without_tags_defaults_to_empty_list(self):
        r = client.post(f"/notes{BASE}", json={"title": "No tags", "body": "Body content here"})
        assert r.status_code == 201
        assert r.json()["tags"] == []

    def test_create_with_empty_tags_list(self):
        r = client.post(f"/notes{BASE}", json={"title": "Empty tags", "body": "Body content here", "tags": []})
        assert r.status_code == 201
        assert r.json()["tags"] == []

    def test_create_response_has_createdAt(self):
        r = client.post(f"/notes{BASE}", json={"title": "Timestamps", "body": "Checking timestamps here"})
        assert "createdAt" in r.json()

    def test_create_response_has_updatedAt(self):
        r = client.post(f"/notes{BASE}", json={"title": "Timestamps", "body": "Checking timestamps here"})
        assert "updatedAt" in r.json()

    def test_create_createdAt_equals_updatedAt_on_new_note(self):
        r = client.post(f"/notes{BASE}", json={"title": "Fresh", "body": "Brand new note body"})
        data = r.json()
        assert data["createdAt"] == data["updatedAt"]

    def test_create_trims_title_whitespace(self):
        r = client.post(f"/notes{BASE}", json={"title": "  Trimmed  ", "body": "Body content here"})
        assert r.status_code == 201
        assert r.json()["title"] == "Trimmed"

    def test_create_trims_body_whitespace(self):
        r = client.post(f"/notes{BASE}", json={"title": "Title", "body": "  Trimmed body  "})
        assert r.status_code == 201
        assert r.json()["body"] == "Trimmed body"

    def test_create_trims_tag_whitespace(self):
        r = client.post(f"/notes{BASE}", json={"title": "Tags", "body": "Body content here", "tags": ["  work  ", " home "]})
        assert r.status_code == 201
        assert r.json()["tags"] == ["work", "home"]

    def test_create_title_at_max_length(self):
        r = client.post(f"/notes{BASE}", json={"title": "A" * 150, "body": "Valid body here"})
        assert r.status_code == 201

    def test_create_body_at_min_length(self):
        r = client.post(f"/notes{BASE}", json={"title": "Min body", "body": "abc"})
        assert r.status_code == 201

    def test_create_body_at_max_length(self):
        r = client.post(f"/notes{BASE}", json={"title": "Max body", "body": "x" * 5000})
        assert r.status_code == 201

    def test_create_multiple_notes_have_unique_ids(self):
        r1 = client.post(f"/notes{BASE}", json={"title": "Note 1", "body": "Body one here"})
        r2 = client.post(f"/notes{BASE}", json={"title": "Note 2", "body": "Body two here"})
        assert r1.json()["id"] != r2.json()["id"]

    # ── Validation Failures (400) ──────────────────────────────────────────────

    def test_create_missing_title_returns_400(self):
        r = client.post(f"/notes{BASE}", json={"body": "Body content here"})
        assert r.status_code == 400

    def test_create_missing_body_returns_400(self):
        r = client.post(f"/notes{BASE}", json={"title": "Title only"})
        assert r.status_code == 400

    def test_create_empty_title_returns_400(self):
        r = client.post(f"/notes{BASE}", json={"title": "", "body": "Body content here"})
        assert r.status_code == 400

    def test_create_whitespace_only_title_returns_400(self):
        # "   ".strip() == "" which violates min_length=1
        r = client.post(f"/notes{BASE}", json={"title": "   ", "body": "Body content here"})
        assert r.status_code == 400

    def test_create_body_too_short_returns_400(self):
        r = client.post(f"/notes{BASE}", json={"title": "Valid", "body": "ab"})
        assert r.status_code == 400

    def test_create_title_too_long_returns_400(self):
        r = client.post(f"/notes{BASE}", json={"title": "A" * 151, "body": "Valid body content"})
        assert r.status_code == 400

    def test_create_body_too_long_returns_400(self):
        r = client.post(f"/notes{BASE}", json={"title": "Title", "body": "x" * 5001})
        assert r.status_code == 400

    def test_create_missing_both_fields_returns_400(self):
        r = client.post(f"/notes{BASE}", json={})
        assert r.status_code == 400

    def test_create_tags_not_array_returns_400(self):
        r = client.post(f"/notes{BASE}", json={"title": "T", "body": "Body here", "tags": "not-an-array"})
        assert r.status_code == 400

    def test_create_error_response_has_error_key(self):
        r = client.post(f"/notes{BASE}", json={"title": "", "body": "Body"})
        assert "error" in r.json()

    def test_create_error_has_code_field(self):
        r = client.post(f"/notes{BASE}", json={"title": "", "body": "Body"})
        assert r.json()["error"]["code"] == "InvalidRequest"

    def test_create_error_has_details_array(self):
        r = client.post(f"/notes{BASE}", json={"title": "", "body": "Body"})
        assert "details" in r.json()["error"]
        assert isinstance(r.json()["error"]["details"], list)

    def test_create_error_detail_has_target_field(self):
        r = client.post(f"/notes{BASE}", json={"title": "", "body": "Body"})
        details = r.json()["error"]["details"]
        targets = [d["target"] for d in details]
        assert "title" in targets

    def test_create_error_has_xms_error_code_header(self):
        r = client.post(f"/notes{BASE}", json={"title": "", "body": "Body"})
        assert "x-ms-error-code" in r.headers

    def test_create_non_json_body_returns_400(self):
        r = client.post(
            f"/notes{BASE}",
            content="not json at all",
            headers={"Content-Type": "application/json"}
        )
        assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# 4. GET /notes — LIST
# ─────────────────────────────────────────────────────────────────────────────

class TestListNotes:

    # ── Success ───────────────────────────────────────────────────────────────

    def test_list_returns_200(self):
        r = client.get(f"/notes{BASE}")
        assert r.status_code == 200

    def test_list_response_has_value_array(self):
        r = client.get(f"/notes{BASE}")
        assert "value" in r.json()
        assert isinstance(r.json()["value"], list)

    def test_list_returns_seeded_notes(self):
        r = client.get(f"/notes{BASE}")
        assert len(r.json()["value"]) == 3

    def test_list_response_has_nextLink_key(self):
        r = client.get(f"/notes{BASE}")
        assert "nextLink" in r.json()

    def test_list_nextLink_is_none_when_all_fit(self):
        r = client.get(f"/notes{BASE}&top=100")
        assert r.json()["nextLink"] is None

    def test_list_each_note_has_required_fields(self):
        r = client.get(f"/notes{BASE}")
        for note in r.json()["value"]:
            assert "id" in note
            assert "title" in note
            assert "body" in note
            assert "tags" in note
            assert "createdAt" in note
            assert "updatedAt" in note

    # ── Pagination (top / skip) ────────────────────────────────────────────────

    def test_list_top_limits_results(self):
        r = client.get(f"/notes{BASE}&top=2")
        assert len(r.json()["value"]) == 2

    def test_list_top_1_returns_one(self):
        r = client.get(f"/notes{BASE}&top=1")
        assert len(r.json()["value"]) == 1

    def test_list_skip_offsets_results(self):
        all_notes = client.get(f"/notes{BASE}&top=100").json()["value"]
        r = client.get(f"/notes{BASE}&skip=1")
        assert r.json()["value"][0]["id"] == all_notes[1]["id"]

    def test_list_top_and_skip_together(self):
        all_notes = client.get(f"/notes{BASE}&top=100").json()["value"]
        r = client.get(f"/notes{BASE}&top=1&skip=2")
        assert r.json()["value"][0]["id"] == all_notes[2]["id"]

    def test_list_skip_beyond_total_returns_empty(self):
        r = client.get(f"/notes{BASE}&skip=999")
        assert r.json()["value"] == []

    def test_list_nextLink_present_when_more_exist(self):
        r = client.get(f"/notes{BASE}&top=2&skip=0")
        assert r.json()["nextLink"] is not None

    def test_list_nextLink_is_string_url(self):
        r = client.get(f"/notes{BASE}&top=1&skip=0")
        link = r.json()["nextLink"]
        assert isinstance(link, str)
        assert link.startswith("http")

    def test_list_nextLink_contains_skip(self):
        r = client.get(f"/notes{BASE}&top=1&skip=0")
        assert "skip=1" in r.json()["nextLink"]

    # ── Pagination (page / limit) — bonus style ────────────────────────────────

    def test_list_page_1_limit_2(self):
        r = client.get(f"/notes{BASE}&page=1&limit=2")
        assert r.status_code == 200
        assert len(r.json()["value"]) == 2

    def test_list_page_2_limit_2(self):
        r = client.get(f"/notes{BASE}&page=2&limit=2")
        assert r.status_code == 200
        assert len(r.json()["value"]) == 1  # 3 notes total, page 2 has 1

    def test_list_page_3_limit_2_returns_empty(self):
        r = client.get(f"/notes{BASE}&page=3&limit=2")
        assert r.json()["value"] == []

    def test_list_limit_takes_priority_over_top(self):
        # limit=1 should override top=100
        r = client.get(f"/notes{BASE}&top=100&limit=1")
        assert len(r.json()["value"]) == 1

    # ── Filtering ─────────────────────────────────────────────────────────────

    def test_list_filter_by_tag_with_single_quotes(self):
        r = client.get(f"/notes{BASE}&filter=tag eq 'fastapi'")
        assert r.status_code == 200
        results = r.json()["value"]
        assert len(results) >= 1
        assert all("fastapi" in n["tags"] for n in results)

    def test_list_filter_by_tag_with_double_quotes(self):
        r = client.get(f'/notes{BASE}&filter=tag eq "fastapi"')
        assert r.status_code == 200
        assert len(r.json()["value"]) >= 1

    def test_list_filter_case_insensitive(self):
        r = client.get(f"/notes{BASE}&filter=tag eq 'FASTAPI'")
        assert r.status_code == 200
        assert len(r.json()["value"]) >= 1

    def test_list_filter_nonexistent_tag_returns_empty(self):
        r = client.get(f"/notes{BASE}&filter=tag eq 'nonexistent-xyz'")
        assert r.status_code == 200
        assert r.json()["value"] == []

    # ── Search ────────────────────────────────────────────────────────────────

    def test_list_search_matches_title(self):
        r = client.get(f"/notes{BASE}&search=Strategy")
        assert r.status_code == 200
        results = r.json()["value"]
        assert len(results) == 1
        assert "Strategy" in results[0]["title"]

    def test_list_search_matches_body(self):
        r = client.get(f"/notes{BASE}&search=Pydantic")
        assert r.status_code == 200
        assert len(r.json()["value"]) >= 1

    def test_list_search_is_case_insensitive(self):
        r = client.get(f"/notes{BASE}&search=strategy")
        assert r.status_code == 200
        assert len(r.json()["value"]) >= 1

    def test_list_search_no_match_returns_empty(self):
        r = client.get(f"/notes{BASE}&search=xyznotexist99")
        assert r.status_code == 200
        assert r.json()["value"] == []

    def test_list_search_and_filter_combined(self):
        r = client.get(f"/notes{BASE}&search=fastapi&filter=tag eq 'welcome'")
        assert r.status_code == 200
        # Should return the welcome note that mentions fastapi
        results = r.json()["value"]
        assert all("welcome" in n["tags"] for n in results)

    # ── Sorting ───────────────────────────────────────────────────────────────

    def test_list_orderby_title_asc(self):
        r = client.get(f"/notes{BASE}&orderby=title asc&top=100")
        titles = [n["title"] for n in r.json()["value"]]
        assert titles == sorted(titles)

    def test_list_orderby_title_desc(self):
        r = client.get(f"/notes{BASE}&orderby=title desc&top=100")
        titles = [n["title"] for n in r.json()["value"]]
        assert titles == sorted(titles, reverse=True)

    def test_list_orderby_createdAt_desc_is_default(self):
        r1 = client.get(f"/notes{BASE}&top=100")
        r2 = client.get(f"/notes{BASE}&top=100&orderby=createdAt desc")
        assert r1.json()["value"] == r2.json()["value"]

    def test_list_orderby_updatedAt(self):
        r = client.get(f"/notes{BASE}&orderby=updatedAt asc&top=100")
        assert r.status_code == 200

    # ── Validation Failures (400) ──────────────────────────────────────────────

    def test_list_top_zero_returns_400(self):
        r = client.get(f"/notes{BASE}&top=0")
        assert r.status_code == 400

    def test_list_top_over_100_returns_400(self):
        r = client.get(f"/notes{BASE}&top=101")
        assert r.status_code == 400

    def test_list_negative_skip_returns_400(self):
        r = client.get(f"/notes{BASE}&skip=-1")
        assert r.status_code == 400

    def test_list_page_zero_returns_400(self):
        r = client.get(f"/notes{BASE}&page=0")
        assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# 5. GET /notes/:id — GET SINGLE
# ─────────────────────────────────────────────────────────────────────────────

class TestGetSingleNote:

    def test_get_existing_note_returns_200(self, first_id):
        r = client.get(f"/notes/{first_id}{BASE}")
        assert r.status_code == 200

    def test_get_returns_correct_id(self, first_id):
        r = client.get(f"/notes/{first_id}{BASE}")
        assert r.json()["id"] == first_id

    def test_get_returns_all_fields(self, first_id):
        r = client.get(f"/notes/{first_id}{BASE}")
        data = r.json()
        for field in ["id", "title", "body", "tags", "createdAt", "updatedAt"]:
            assert field in data

    def test_get_nonexistent_id_returns_404(self):
        r = client.get(f"/notes/does-not-exist{BASE}")
        assert r.status_code == 404

    def test_get_404_error_shape(self):
        r = client.get(f"/notes/does-not-exist{BASE}")
        body = r.json()
        assert "error" in body
        assert body["error"]["code"] == "ResourceNotFound"

    def test_get_404_has_xms_error_code_header(self):
        r = client.get(f"/notes/does-not-exist{BASE}")
        assert r.headers.get("x-ms-error-code") == "ResourceNotFound"

    def test_get_404_message_contains_id(self):
        r = client.get(f"/notes/my-fake-id{BASE}")
        assert "my-fake-id" in r.json()["error"]["message"]

    def test_get_note_created_via_post(self):
        note = make_note("Created", "Body of created note here")
        r = client.get(f"/notes/{note['id']}{BASE}")
        assert r.status_code == 200
        assert r.json()["title"] == "Created"

    def test_get_after_delete_returns_404(self, first_id):
        client.delete(f"/notes/{first_id}{BASE}")
        r = client.get(f"/notes/{first_id}{BASE}")
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# 6. PUT /notes/:id — FULL REPLACE
# ─────────────────────────────────────────────────────────────────────────────

class TestReplaceNote:

    # ── Success ───────────────────────────────────────────────────────────────

    def test_put_returns_200(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "New Title", "body": "New body content."})
        assert r.status_code == 200

    def test_put_updates_title(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "Updated Title", "body": "Updated body here."})
        assert r.json()["title"] == "Updated Title"

    def test_put_updates_body(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "Title", "body": "Brand new body text."})
        assert r.json()["body"] == "Brand new body text."

    def test_put_updates_tags(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "T", "body": "Body here.", "tags": ["new"]})
        assert r.json()["tags"] == ["new"]

    def test_put_without_tags_clears_tags(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "T", "body": "Body here."})
        assert r.json()["tags"] == []

    def test_put_preserves_id(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "T", "body": "Body here."})
        assert r.json()["id"] == first_id

    def test_put_preserves_createdAt(self, first_id):
        original = client.get(f"/notes/{first_id}{BASE}").json()["createdAt"]
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "T", "body": "Body here."})
        assert r.json()["createdAt"] == original

    def test_put_updates_updatedAt(self, first_id):
        original = client.get(f"/notes/{first_id}{BASE}").json()["updatedAt"]
        import time; time.sleep(0.01)
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "T", "body": "Body here."})
        assert r.json()["updatedAt"] >= original

    def test_put_is_idempotent(self, first_id):
        payload = {"title": "Same", "body": "Same body content."}
        r1 = client.put(f"/notes/{first_id}{BASE}", json=payload)
        r2 = client.put(f"/notes/{first_id}{BASE}", json=payload)
        assert r1.json()["title"] == r2.json()["title"]
        assert r1.json()["body"] == r2.json()["body"]

    def test_put_trims_title(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "  Trimmed  ", "body": "Body here."})
        assert r.json()["title"] == "Trimmed"

    # ── Validation Failures (400) ──────────────────────────────────────────────

    def test_put_missing_title_returns_400(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"body": "Body here."})
        assert r.status_code == 400

    def test_put_missing_body_returns_400(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "Title"})
        assert r.status_code == 400

    def test_put_empty_title_returns_400(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "", "body": "Body here."})
        assert r.status_code == 400

    def test_put_body_too_short_returns_400(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "Title", "body": "ab"})
        assert r.status_code == 400

    def test_put_title_too_long_returns_400(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "A" * 151, "body": "Body here."})
        assert r.status_code == 400

    def test_put_error_shape(self, first_id):
        r = client.put(f"/notes/{first_id}{BASE}", json={"title": "", "body": "Body"})
        assert r.json()["error"]["code"] == "InvalidRequest"

    # ── Not Found (404) ────────────────────────────────────────────────────────

    def test_put_nonexistent_id_returns_404(self):
        r = client.put(f"/notes/fake-id{BASE}", json={"title": "T", "body": "Body here."})
        assert r.status_code == 404

    def test_put_404_error_shape(self):
        r = client.put(f"/notes/fake-id{BASE}", json={"title": "T", "body": "Body here."})
        assert r.json()["error"]["code"] == "ResourceNotFound"


# ─────────────────────────────────────────────────────────────────────────────
# 7. PATCH /notes/:id — PARTIAL UPDATE
# ─────────────────────────────────────────────────────────────────────────────

class TestPatchNote:

    # ── Success ───────────────────────────────────────────────────────────────

    def test_patch_returns_200(self, first_id):
        r = client.patch(f"/notes/{first_id}{BASE}", json={"title": "Patched Title"})
        assert r.status_code == 200

    def test_patch_title_only_preserves_body(self, first_id):
        original_body = client.get(f"/notes/{first_id}{BASE}").json()["body"]
        r = client.patch(f"/notes/{first_id}{BASE}", json={"title": "New Title"})
        assert r.json()["title"] == "New Title"
        assert r.json()["body"] == original_body

    def test_patch_body_only_preserves_title(self, first_id):
        original_title = client.get(f"/notes/{first_id}{BASE}").json()["title"]
        r = client.patch(f"/notes/{first_id}{BASE}", json={"body": "New body content here."})
        assert r.json()["body"] == "New body content here."
        assert r.json()["title"] == original_title

    def test_patch_tags_only_preserves_title_and_body(self, first_id):
        original = client.get(f"/notes/{first_id}{BASE}").json()
        r = client.patch(f"/notes/{first_id}{BASE}", json={"tags": ["patched"]})
        assert r.json()["tags"] == ["patched"]
        assert r.json()["title"] == original["title"]
        assert r.json()["body"] == original["body"]

    def test_patch_tags_to_empty_list(self, first_id):
        r = client.patch(f"/notes/{first_id}{BASE}", json={"tags": []})
        assert r.status_code == 200
        assert r.json()["tags"] == []

    def test_patch_all_fields_at_once(self, first_id):
        r = client.patch(f"/notes/{first_id}{BASE}", json={
            "title": "All patched",
            "body": "All body patched here.",
            "tags": ["x"]
        })
        assert r.status_code == 200
        assert r.json()["title"] == "All patched"
        assert r.json()["tags"] == ["x"]

    def test_patch_preserves_id(self, first_id):
        r = client.patch(f"/notes/{first_id}{BASE}", json={"title": "New"})
        assert r.json()["id"] == first_id

    def test_patch_preserves_createdAt(self, first_id):
        original = client.get(f"/notes/{first_id}{BASE}").json()["createdAt"]
        r = client.patch(f"/notes/{first_id}{BASE}", json={"title": "New"})
        assert r.json()["createdAt"] == original

    def test_patch_updates_updatedAt(self, first_id):
        original = client.get(f"/notes/{first_id}{BASE}").json()["updatedAt"]
        import time; time.sleep(0.01)
        r = client.patch(f"/notes/{first_id}{BASE}", json={"title": "New"})
        assert r.json()["updatedAt"] >= original

    def test_patch_trims_title(self, first_id):
        r = client.patch(f"/notes/{first_id}{BASE}", json={"title": "  Spaced  "})
        assert r.json()["title"] == "Spaced"

    def test_patch_is_idempotent(self, first_id):
        payload = {"title": "Stable Title"}
        r1 = client.patch(f"/notes/{first_id}{BASE}", json=payload)
        r2 = client.patch(f"/notes/{first_id}{BASE}", json=payload)
        assert r1.json()["title"] == r2.json()["title"]

    # ── Validation Failures (400) ──────────────────────────────────────────────

    def test_patch_empty_payload_returns_400(self, first_id):
        r = client.patch(f"/notes/{first_id}{BASE}", json={})
        assert r.status_code == 400

    def test_patch_empty_payload_error_message(self, first_id):
        r = client.patch(f"/notes/{first_id}{BASE}", json={})
        details = r.json()["error"]["details"]
        messages = [d["message"].lower() for d in details]
        assert any("at least one" in m for m in messages)

    def test_patch_empty_title_returns_400(self, first_id):
        r = client.patch(f"/notes/{first_id}{BASE}", json={"title": ""})
        assert r.status_code == 400

    def test_patch_title_too_long_returns_400(self, first_id):
        r = client.patch(f"/notes/{first_id}{BASE}", json={"title": "A" * 151})
        assert r.status_code == 400

    def test_patch_body_too_short_returns_400(self, first_id):
        r = client.patch(f"/notes/{first_id}{BASE}", json={"body": "ab"})
        assert r.status_code == 400

    def test_patch_body_too_long_returns_400(self, first_id):
        r = client.patch(f"/notes/{first_id}{BASE}", json={"body": "x" * 5001})
        assert r.status_code == 400

    def test_patch_unknown_fields_only_returns_400(self, first_id):
        # No valid patchable field provided
        r = client.patch(f"/notes/{first_id}{BASE}", json={"unknown_field": "value"})
        assert r.status_code == 400

    # ── Not Found (404) ────────────────────────────────────────────────────────

    def test_patch_nonexistent_id_returns_404(self):
        r = client.patch(f"/notes/fake-id{BASE}", json={"title": "New Title"})
        assert r.status_code == 404

    def test_patch_404_error_shape(self):
        r = client.patch(f"/notes/fake-id{BASE}", json={"title": "New"})
        assert r.json()["error"]["code"] == "ResourceNotFound"


# ─────────────────────────────────────────────────────────────────────────────
# 8. DELETE /notes/:id
# ─────────────────────────────────────────────────────────────────────────────

class TestDeleteNote:

    def test_delete_existing_returns_200(self, first_id):
        r = client.delete(f"/notes/{first_id}{BASE}")
        assert r.status_code == 200

    def test_delete_response_has_message(self, first_id):
        r = client.delete(f"/notes/{first_id}{BASE}")
        assert "message" in r.json()

    def test_delete_message_contains_deleted_successfully(self, first_id):
        r = client.delete(f"/notes/{first_id}{BASE}")
        assert "deleted successfully" in r.json()["message"].lower()

    def test_delete_removes_note_from_store(self, first_id):
        client.delete(f"/notes/{first_id}{BASE}")
        r = client.get(f"/notes/{first_id}{BASE}")
        assert r.status_code == 404

    def test_delete_twice_returns_404_second_time(self, first_id):
        client.delete(f"/notes/{first_id}{BASE}")
        r = client.delete(f"/notes/{first_id}{BASE}")
        assert r.status_code == 404

    def test_delete_nonexistent_id_returns_404(self):
        r = client.delete(f"/notes/does-not-exist{BASE}")
        assert r.status_code == 404

    def test_delete_404_error_shape(self):
        r = client.delete(f"/notes/does-not-exist{BASE}")
        assert "error" in r.json()
        assert r.json()["error"]["code"] == "ResourceNotFound"

    def test_delete_all_notes_one_by_one(self, seeded_ids):
        for note_id in seeded_ids:
            r = client.delete(f"/notes/{note_id}{BASE}")
            assert r.status_code == 200
        r = client.get(f"/notes{BASE}")
        assert r.json()["value"] == []


# ─────────────────────────────────────────────────────────────────────────────
# 9. POST /notes/bulk — BULK CREATE
# ─────────────────────────────────────────────────────────────────────────────

class TestBulkCreate:

    # ── Success ───────────────────────────────────────────────────────────────

    def test_bulk_create_returns_201(self):
        payload = [
            {"title": "Bulk A", "body": "Body of bulk A"},
            {"title": "Bulk B", "body": "Body of bulk B"},
        ]
        r = client.post(f"/notes/bulk{BASE}", json=payload)
        assert r.status_code == 201

    def test_bulk_create_response_has_value_array(self):
        payload = [{"title": "B1", "body": "Body one here"}]
        r = client.post(f"/notes/bulk{BASE}", json=payload)
        assert "value" in r.json()
        assert isinstance(r.json()["value"], list)

    def test_bulk_create_returns_all_notes(self):
        payload = [
            {"title": "B1", "body": "Body one here"},
            {"title": "B2", "body": "Body two here"},
            {"title": "B3", "body": "Body three here"},
        ]
        r = client.post(f"/notes/bulk{BASE}", json=payload)
        assert len(r.json()["value"]) == 3

    def test_bulk_create_each_note_has_id(self):
        payload = [{"title": "B1", "body": "Body one here"}, {"title": "B2", "body": "Body two here"}]
        r = client.post(f"/notes/bulk{BASE}", json=payload)
        for note in r.json()["value"]:
            assert "id" in note

    def test_bulk_create_ids_are_unique(self):
        payload = [{"title": "B1", "body": "Body one here"}, {"title": "B2", "body": "Body two here"}]
        r = client.post(f"/notes/bulk{BASE}", json=payload)
        ids = [n["id"] for n in r.json()["value"]]
        assert len(ids) == len(set(ids))

    def test_bulk_create_correct_titles_in_order(self):
        payload = [{"title": "First", "body": "Body first"}, {"title": "Second", "body": "Body second"}]
        r = client.post(f"/notes/bulk{BASE}", json=payload)
        notes = r.json()["value"]
        assert notes[0]["title"] == "First"
        assert notes[1]["title"] == "Second"

    def test_bulk_create_with_tags(self):
        payload = [{"title": "Tagged", "body": "Body here", "tags": ["bulk", "test"]}]
        r = client.post(f"/notes/bulk{BASE}", json=payload)
        assert r.json()["value"][0]["tags"] == ["bulk", "test"]

    def test_bulk_create_single_note(self):
        payload = [{"title": "Solo", "body": "Just one note"}]
        r = client.post(f"/notes/bulk{BASE}", json=payload)
        assert r.status_code == 201
        assert len(r.json()["value"]) == 1

    def test_bulk_create_notes_appear_in_list(self):
        payload = [{"title": "Bulk list check", "body": "Should appear in list"}]
        r = client.post(f"/notes/bulk{BASE}", json=payload)
        new_id = r.json()["value"][0]["id"]
        r2 = client.get(f"/notes/{new_id}{BASE}")
        assert r2.status_code == 200

    def test_bulk_create_increases_total_count(self):
        before = len(client.get(f"/notes{BASE}&top=100").json()["value"])
        payload = [{"title": "B1", "body": "Body one"}, {"title": "B2", "body": "Body two"}]
        client.post(f"/notes/bulk{BASE}", json=payload)
        after = len(client.get(f"/notes{BASE}&top=100").json()["value"])
        assert after == before + 2

    # ── Validation Failures (400) ──────────────────────────────────────────────

    def test_bulk_create_one_invalid_item_returns_400(self):
        payload = [
            {"title": "Valid", "body": "Valid body here"},
            {"title": "", "body": "Invalid title"}
        ]
        r = client.post(f"/notes/bulk{BASE}", json=payload)
        assert r.status_code == 400

    # ── Header Check ──

    def test_xms_request_id_present(self):
        r = client.get(f"/notes{BASE}")
        assert "x-ms-request-id" in r.headers
