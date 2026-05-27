import pytest
import random
import httpx
import uuid
import asyncio
from src.main import app
from src.database import get_db, engine

API_VERSION = "2024-05-25"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def ac():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

async def get_auth_headers(ac, email, password):
    resp = await ac.post(f"/auth/login?api-version={API_VERSION}", json={"email": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
class TestFullSystem:
    
    async def test_auth_and_notes_flow(self, ac):
        # 1. Register
        email = f"user_{random.randint(1000, 9999)}@example.com"
        pw = "Password123!"
        resp = await ac.post(f"/auth/register?api-version={API_VERSION}", json={"email": email, "password": pw})
        assert resp.status_code == 201
        
        # 2. Login
        headers = await get_auth_headers(ac, email, pw)
        
        # 3. Create Note
        note_data = {"title": "Test Note", "body": "Test Body content", "tags": ["tag1"]}
        resp = await ac.post(f"/notes?api-version={API_VERSION}", json=note_data, headers=headers)
        assert resp.status_code == 201
        note_id = resp.json()["id"]
        
        # 4. List Notes
        resp = await ac.get(f"/notes?api-version={API_VERSION}", headers=headers)
        assert resp.status_code == 200
        assert any(n["id"] == note_id for n in resp.json()["value"])

        # 5. Patch Note
        resp = await ac.patch(f"/notes/{note_id}?api-version={API_VERSION}", json={"title": "Updated"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"

    async def test_rbac_restrictions(self, ac):
        # 1. Register normal user
        email = f"victim_{random.randint(1000, 9999)}@example.com"
        pw = "Password123!"
        await ac.post(f"/auth/register?api-version={API_VERSION}", json={"email": email, "password": pw})
        headers = await get_auth_headers(ac, email, pw)
        
        # 2. Try to access admin area
        resp = await ac.get(f"/admin/users?api-version={API_VERSION}", headers=headers)
        assert resp.status_code == 403

    async def test_admin_powers(self, ac):
        # Using the admin account seeded in previous steps
        admin_headers = await get_auth_headers(ac, "admin@example.com", "AdminPassword123!")
        
        # 1. List users
        resp = await ac.get(f"/admin/users?api-version={API_VERSION}", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_api_version_enforcement(self, ac):
        # Missing version
        resp = await ac.get("/health")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "MissingApiVersion"
        
        # Invalid version
        resp = await ac.get("/health?api-version=invalid")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "UnsupportedApiVersion"

    async def test_token_rotation(self, ac):
        email = f"rotate_{random.randint(1000, 9999)}@example.com"
        pw = "Password123!"
        await ac.post(f"/auth/register?api-version={API_VERSION}", json={"email": email, "password": pw})
        
        # Login to get refresh token
        resp = await ac.post(f"/auth/login?api-version={API_VERSION}", json={"email": email, "password": pw})
        refresh_token = resp.json()["refreshToken"]
        
        # Rotate
        resp = await ac.post(f"/auth/refresh?api-version={API_VERSION}", json={"refreshToken": refresh_token})
        assert resp.status_code == 200
        new_refresh = resp.json()["refreshToken"]
        assert new_refresh != refresh_token
        
        # Old one should fail
        resp = await ac.post(f"/auth/refresh?api-version={API_VERSION}", json={"refreshToken": refresh_token})
        assert resp.status_code == 401
