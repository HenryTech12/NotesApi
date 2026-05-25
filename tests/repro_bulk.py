
import requests
import json
import os

def test_bulk_request():
    url = "http://localhost:3000/notes/bulk"
    params = {"api-version": "2024-05-25"}
    
    file_path = os.path.join("artifacts", "bulk_notes_data.json")
    with open(file_path, "r") as f:
        data = json.load(f)
    
    print(f"Sending bulk request with {len(data)} items...")
    try:
        response = requests.post(url, params=params, json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            print("Success! Created items count:", len(response.json()["value"]))
        else:
            print("Error response:", response.text)
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_bulk_request()
