import httpx
import sys
import random

BASE_URL = "http://localhost:3000"
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
        
    print("\nALL BASIC TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_api()
