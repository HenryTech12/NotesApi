import httpx
import sys
import random

BASE_URL = "https://notesapi-sgvx.onrender.com"
API_VERSION = "2024-05-25"

def test_api():
    # Increase timeout for cloud DB operations
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    
    # 1. Health check
    print("Testing /health...")
    r = client.get(f"/health?api-version={API_VERSION}")
    print(f"Status: {r.status_code}, Body: {r.json()}")
    if r.status_code != 200:
        sys.exit(1)
        
    # 2. Register
    print("\nTesting /auth/register...")
    email = f"test_{random.randint(1000, 9999)}@example.com"
    password = "Password123!"
    r = client.post(
        f"/auth/register?api-version={API_VERSION}",
        json={"email": email, "password": password}
    )
    print(f"Status: {r.status_code}, Body: {r.json()}")
    if r.status_code not in [201, 409]: # 409 if already exists
        sys.exit(1)
        
    # 3. Login
    print("\nTesting /auth/login...")
    r = client.post(
        f"/auth/login?api-version={API_VERSION}",
        json={"email": email, "password": password}
    )
    print(f"Status: {r.status_code}, Body: {r.json()}")
    if r.status_code != 200:
        sys.exit(1)
    
    tokens = r.json()
    # The login response in auth.py returns {"accessToken": ..., "refreshToken": ...} because of alias_generator!
    access_token = tokens.get("accessToken") or tokens.get("access_token")
    if not access_token:
        print("Could not find access token in response")
        sys.exit(1)
    print("Login successful.")
    
    # 4. Create Note
    print("\nTesting /notes (Create)...")
    headers = {"Authorization": f"Bearer {access_token}"}
    note_payload = {"title": "Test Live Note", "body": "This is a note from the verify script."}
    r = client.post(
        f"/notes?api-version={API_VERSION}",
        json=note_payload,
        headers=headers
    )
    print(f"Status: {r.status_code}, Body: {r.json()}")
    if r.status_code != 201:
        sys.exit(1)
    
    note_id = r.json()["id"]
    
    # 5. List Notes
    print("\nTesting /notes (List)...")
    r = client.get(f"/notes?api-version={API_VERSION}", headers=headers)
    print(f"Status: {r.status_code}, Count: {len(r.json()['value'])}")
    if r.status_code != 200:
        sys.exit(1)
        
    # 6. Bulk Create
    print("\nTesting /notes/bulk (Bulk)...")
    bulk_payload = [
        {"title": "Bulk Note 1", "body": "Body 1"},
        {"title": "Bulk Note 2", "body": "Body 2"}
    ]
    r = client.post(
        f"/notes/bulk?api-version={API_VERSION}",
        json=bulk_payload,
        headers=headers
    )
    print(f"Status: {r.status_code}, Body: {r.json()}")
    if r.status_code != 201:
        sys.exit(1)

    # 7. Patch Note
    print(f"\nTesting /notes/{note_id} (Patch)...")
    r = client.patch(
        f"/notes/{note_id}?api-version={API_VERSION}",
        json={"title": "Patched Live Title"},
        headers=headers
    )
    print(f"Status: {r.status_code}, Body: {r.json()}")
    if r.status_code != 200:
        sys.exit(1)

    # 8. Delete Note
    print(f"\nTesting /notes/{note_id} (Delete)...")
    r = client.delete(
        f"/notes/{note_id}?api-version={API_VERSION}",
        headers=headers
    )
    print(f"Status: {r.status_code}, Body: {r.json()}")
    if r.status_code != 200:
        sys.exit(1)

    # 9. PUT Note
    print("\nTesting /notes (Create for PUT)...")
    r = client.post(
        f"/notes?api-version={API_VERSION}",
        json={"title": "To be replaced", "body": "Original body"},
        headers=headers
    )
    put_id = r.json()["id"]
    print(f"Testing /notes/{put_id} (Put)...")
    r = client.put(
        f"/notes/{put_id}?api-version={API_VERSION}",
        json={"title": "Replaced Title", "body": "Replaced Body", "tags": ["replacement"]},
        headers=headers
    )
    print(f"Status: {r.status_code}, Body: {r.json()}")
    if r.status_code != 200:
        sys.exit(1)

    print("\nALL TESTS PASSED SUCCESSFULLY INCLUDING BULK, PATCH, DELETE AND PUT!")

if __name__ == "__main__":
    test_api()
