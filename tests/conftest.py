# tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.database import Base, get_db
from src.main import app
from src.models.user import User
from src.services.auth_service import hash_password

# Use a local SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed admin user
    async with AsyncSessionLocal() as session:
        admin_user = User(
            email="admin@example.com",
            password_hash=hash_password("AdminPassword123!"),
            role="admin"
        )
        session.add(admin_user)
        await session.commit()
        
    yield
    # No cleanup for session scope to allow inspection if needed, or drop all here
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

async def override_get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db
