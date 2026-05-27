import pytest
import random
import httpx
import asyncio
from src.main import app
from src.database import get_db, engine

# Setup async test client
API_VERSION = "2024-05-25"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def async_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await engine.dispose()

async def get_tokens(client, email, password):
    r = await client.post(
        f"/auth/login?api-version={API_VERSION}",
        json={"email": email, "password": password}
    )
    if r.status_code != 200:
        print(f"Login failed: {r.text}")
    assert r.status_code == 200
    data = r.json()
    return data["accessToken"], data["refreshToken"]

@pytest.mark.asyncio
class TestAdminFeatures:
    
    async def test_admin_full_flow(self, async_client):
        # 1. Register user
        email = f"user_{random.randint(1000, 9999)}@example.com"
        pw = "Password123!"
        reg = await async_client.post(
            f"/auth/register?api-version={API_VERSION}",
            json={"email": email, "password": pw}
        )
        assert reg.status_code == 201
        user_id = reg.json()["id"]

        # 2. Login as admin
        # Using the admin credentials from previous setup
        admin_token, _ = await get_tokens(async_client, "admin@example.com", "AdminPassword123!")
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 3. Flag user
        flag_res = await async_client.patch(
            f"/admin/users/{user_id}/flag?api-version={API_VERSION}",
            headers=headers,
            json={"isFlagged": True}
        )
        assert flag_res.status_code == 200
        assert flag_res.json()["isFlagged"] is True

        # 4. Verify user is blocked from accessing notes
        user_token, _ = await get_tokens(async_client, email, pw)
        blocked_res = await async_client.get(
            f"/notes?api-version={API_VERSION}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert blocked_res.status_code == 403
        content = blocked_res.json()
        # The error format might be nested based on error_handler.py or middleware
        assert "AccountSuspended" in str(content)

        # 5. Unflag user
        unflag_res = await async_client.patch(
            f"/admin/users/{user_id}/flag?api-version={API_VERSION}",
            headers=headers,
            json={"isFlagged": False}
        )
        assert unflag_res.status_code == 200
        assert unflag_res.json()["isFlagged"] is False

        # 6. Verify user can access again
        unblocked_res = await async_client.get(
            f"/notes?api-version={API_VERSION}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert unblocked_res.status_code == 200

        # 7. Change role to admin
        role_res = await async_client.patch(
            f"/admin/users/{user_id}/role?api-version={API_VERSION}",
            headers=headers,
            json={"role": "admin"}
        )
        assert role_res.status_code == 200
        assert role_res.json()["role"] == "admin"

        # 8. View all notes (privacy override)
        notes_res = await async_client.get(
            f"/admin/notes?api-version={API_VERSION}",
            headers=headers
        )
        assert notes_res.status_code == 200
        assert "value" in notes_res.json()

        # 9. Delete user
        del_res = await async_client.delete(
            f"/admin/users/{user_id}?api-version={API_VERSION}",
            headers=headers
        )
        assert del_res.status_code == 200
        
        # 10. Verify user is gone
        get_res = await async_client.get(
            f"/admin/users/{user_id}?api-version={API_VERSION}",
            headers=headers
        )
        assert get_res.status_code == 404
