# src/utils/store.py
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict

def get_azure_timestamp():
    # Azure likes RFC 3339 with up to 3 fractional seconds and 'Z' suffix
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

class Store:
    def __init__(self):
        self.notes: Dict[str, dict] = {}

    def create(self, title: str, body: str, tags: List[str] = None) -> dict:
        now = get_azure_timestamp()
        note_id = str(uuid.uuid4())
        note = {
            "id": note_id,
            "title": title.strip(),
            "body": body.strip(),
            "tags": [t.strip() for t in (tags or [])],
            "createdAt": now,
            "updatedAt": now,
        }
        self.notes[note_id] = note
        return note

    def find_by_id(self, note_id: str) -> Optional[dict]:
        return self.notes.get(note_id)

    def find_all(self) -> List[dict]:
        return list(self.notes.values())

    def replace(self, note_id: str, title: str, body: str, tags: List[str] = None) -> Optional[dict]:
        if note_id not in self.notes:
            return None
        
        existing = self.notes[note_id]
        updated_note = {
            **existing,
            "title": title.strip(),
            "body": body.strip(),
            "tags": [t.strip() for t in (tags or [])],
            "updatedAt": get_azure_timestamp(),
        }
        self.notes[note_id] = updated_note
        return updated_note

    def patch(self, note_id: str, fields: dict) -> Optional[dict]:
        if note_id not in self.notes:
            return None
        
        existing = self.notes[note_id]
        updated_note = existing.copy()
        
        if "title" in fields:
            updated_note["title"] = fields["title"].strip()
        if "body" in fields:
            updated_note["body"] = fields["body"].strip()
        if "tags" in fields:
            # Handle list trimming or empty list
            tags_val = fields["tags"] or []
            updated_note["tags"] = [t.strip() for t in tags_val]
            
        updated_note["updatedAt"] = get_azure_timestamp()
        self.notes[note_id] = updated_note
        return updated_note

    def remove(self, note_id: str) -> bool:
        if note_id in self.notes:
            del self.notes[note_id]
            return True
        return False

    def seed(self):
        self.create(
            title="Welcome to the Notes API (Python)",
            body="This is your first note in FastAPI. Enjoy the speed and type safety!",
            tags=["welcome", "fastapi"]
        )
        self.create(
            title="Hackathon Strategy",
            body="Focus on Pydantic for validation and consistent response shapes.",
            tags=["hackathon", "strategy"]
        )
        self.create(
            title="Final Task",
            body="Ensure all endpoints match the required status codes and schema.",
            tags=["todo", "final"]
        )

store = Store()
