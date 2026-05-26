# src/services/note_service.py
from sqlalchemy import select, delete, update, func, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.note import Note
from src.models.user import User
from typing import List, Optional, Any
import uuid

class NoteService:
    @staticmethod
    async def list_notes(
        db: AsyncSession,
        user: User,
        top: int = 10,
        skip: int = 0,
        orderby: str = "created_at desc",
        filter_str: Optional[str] = None,
        search: Optional[str] = None,
        is_admin: bool = False
    ) -> tuple[List[Note], int]:
        stmt = select(Note)
        
        # Ownership filter
        if not is_admin:
            stmt = stmt.where(Note.user_id == user.id)
            
        # OData-style filter (tag eq 'val')
        if filter_str:
            import re
            match = re.search(r"tag eq ['\"](.+?)['\"]", filter_str, re.IGNORECASE)
            if match:
                tag_val = match.group(1)
                # PostgreSQL ANY for ARRAY
                stmt = stmt.where(Note.tags.any(tag_val))
            elif "tag eq " in filter_str.lower():
                tag_val = filter_str.lower().split("tag eq ")[1].strip()
                stmt = stmt.where(Note.tags.any(tag_val))

        # Search
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(or_(
                Note.title.ilike(search_pattern),
                Note.body.ilike(search_pattern)
            ))

        # Sorting
        if orderby:
            parts = orderby.split()
            field_name = parts[0]
            # Map camelCase to snake_case if necessary, but here we assume snake_case for DB
            direction = parts[1].lower() if len(parts) > 1 else "asc"
            
            column = getattr(Note, field_name, Note.created_at)
            if direction == "desc":
                stmt = stmt.order_by(column.desc())
            else:
                stmt = stmt.order_by(column.asc())
        
        # Get count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0
        
        # Pagination
        stmt = stmt.offset(skip).limit(top)
        
        result = await db.execute(stmt)
        return list(result.scalars().all()), total

    @staticmethod
    async def create_note(db: AsyncSession, user_id: uuid.UUID, title: str, body: str, tags: List[str]) -> Note:
        note = Note(user_id=user_id, title=title, body=body, tags=tags)
        db.add(note)
        await db.flush()
        return note

    @staticmethod
    async def get_note(db: AsyncSession, note_id: str, user: User, is_admin: bool = False) -> Optional[Note]:
        try:
            uid = uuid.UUID(note_id)
        except ValueError:
            return None
            
        stmt = select(Note).where(Note.id == uid)
        if not is_admin:
            stmt = stmt.where(Note.user_id == user.id)
            
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    @staticmethod
    async def update_note(db: AsyncSession, note_id: str, user: User, data: dict, is_admin: bool = False) -> Optional[Note]:
        note = await NoteService.get_note(db, note_id, user, is_admin)
        if not note:
            return None
            
        allowed_keys = {"title", "body", "tags"}
        for key, value in data.items():
            if key in allowed_keys:
                setattr(note, key, value)
        
        # Use a plain datetime for updated_at to avoid func.now() issues with some drivers/states
        from datetime import datetime
        note.updated_at = datetime.utcnow()
        await db.flush()
        return note

    @staticmethod
    async def delete_note(db: AsyncSession, note_id: str, user: User, is_admin: bool = False) -> bool:
        note = await NoteService.get_note(db, note_id, user, is_admin)
        if not note:
            return False
            
        await db.delete(note)
        await db.flush()
        return True

    @staticmethod
    async def create_notes_bulk(db: AsyncSession, user_id: uuid.UUID, notes_data: List[Any]) -> List[Note]:
        created = []
        for nd in notes_data:
            note = Note(
                user_id=user_id,
                title=nd.title,
                body=nd.body,
                tags=nd.tags
            )
            db.add(note)
            created.append(note)
        await db.flush()
        return created
