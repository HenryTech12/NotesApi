# tests/test_auth_db.py
import pytest
import asyncio
import random
import os
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.main import app
from src.database import get_db, Base
from src.models.user import User

# Test Database URL
TEST_DATABASE_URL = os.getenv("DATABASE_URL")

# Engine and Sessionmaker for tests
engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Helper to run async code in a synchronous context
    def run_async(coro):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    run_async(_setup())
    
    async def override_get_db():
        # Create a fresh engine/session FOR EVERY REQUEST
        # This is slower but guarantees no connection sharing/loop conflicts in TestClient
        local_engine = create_async_engine(TEST_DATABASE_URL)
        async_session = async_sessionmaker(local_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
                await local_engine.dispose()

    app.dependency_overrides[get_db] = override_get_db
    yield

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

API_VERSION = "2024-05-25"

class TestAuthentication:
    def test_register_success(self, client: TestClient):
        email = f"test_{random.randint(10000, 99999)}@example.com"
        response = client.post(
            f"/auth/register?api-version={API_VERSION}",
            json={"email": email, "password": "Password123!"}
        )
        assert response.status_code == 201
        assert response.json()["email"] == email

    def test_register_duplicate_email(self, client: TestClient):
        email = f"dup_{random.randint(10000, 99999)}@example.com"
        client.post(
            f"/auth/register?api-version={API_VERSION}",
            json={"email": email, "password": "Password123!"}
        )
        response = client.post(
            f"/auth/register?api-version={API_VERSION}",
            json={"email": email, "password": "Password123!"}
        )
        assert response.status_code == 409

    def test_login_success(self, client: TestClient):
        email = f"login_{random.randint(10000, 99999)}@example.com"
        password = "Password123!"
        client.post(
            f"/auth/register?api-version={API_VERSION}",
            json={"email": email, "password": password}
        )
        response = client.post(
            f"/auth/login?api-version={API_VERSION}",
            json={"email": email, "password": password}
        )
        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data or "access_token" in data

    def test_login_invalid_credentials(self, client: TestClient):
        response = client.post(
            f"/auth/login?api-version={API_VERSION}",
            json={"email": "wrong@example.com", "password": "Password123!"}
        )
        assert response.status_code == 401

class TestNoteOwnership:
    def get_token(self, client: TestClient, email: str):
        password = "Password123!"
        client.post(f"/auth/register?api-version={API_VERSION}", json={"email": email, "password": password})
        res = client.post(f"/auth/login?api-version={API_VERSION}", json={"email": email, "password": password})
        data = res.json()
        return data.get("accessToken") or data.get("access_token")

    def test_user_cannot_see_others_notes(self, client: TestClient):
        t1 = self.get_token(client, f"u1_{random.randint(10000, 99999)}@example.com")
        t2 = self.get_token(client, f"u2_{random.randint(10000, 99999)}@example.com")
        client.post(f"/notes?api-version={API_VERSION}", headers={"Authorization": f"Bearer {t1}"}, json={"title": "N1", "body": "B1"})
        res = client.get(f"/notes?api-version={API_VERSION}", headers={"Authorization": f"Bearer {t2}"})
        assert res.status_code == 200
        assert len(res.json().get("value", [])) == 0

    def test_admin_can_see_all_notes(self, client: TestClient):
        t1 = self.get_token(client, f"u3_{random.randint(10000, 99999)}@example.com")
        client.post(f"/notes?api-version={API_VERSION}", headers={"Authorization": f"Bearer {t1}"}, json={"title": "N1", "body": "B1"})
        
        loop = asyncio.get_event_loop()
        admin_email = f"admin_{random.randint(10000, 99999)}@example.com"
        async def _create_admin():
            async with TestingSessionLocal() as db:
                admin = User(email=admin_email, password_hash="...", role="admin")
                db.add(admin)
                await db.commit()
                await db.refresh(admin)
                return admin.id
        admin_id = loop.run_until_complete(_create_admin())
        from src.services.auth_service import create_access_token
        admin_token = create_access_token({"sub": str(admin_id), "email": admin_email, "role": "admin"})

        res = client.get(f"/notes?api-version={API_VERSION}", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert len(res.json().get("value", [])) > 0
