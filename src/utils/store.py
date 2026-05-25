# src/utils/store.py
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict

class Store:
    def __init__(self):
        self.notes: Dict[str, dict] = {}

    def create(self, title: str, body: str, tags: List[str] = None) -> dict:
        now = datetime.now(timezone.utc).isoformat()
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
            "updatedAt": datetime.now(timezone.utc).isoformat(),
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
            updated_note["tags"] = [t.strip() for t in fields["tags"]]
            
        updated_note["updatedAt"] = datetime.now(timezone.utc).isoformat()
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
