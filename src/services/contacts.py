from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repository.contacts import ContactRepository
from src.database.models import User
from src.schemas import ContactModel

from fastapi import HTTPException, status


def _handle_integrity_error():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Помилка цілісності даних.",
    )


class ContactsService:
    def __init__(self, db: AsyncSession):
        self.repository = ContactRepository(db)

    async def create_contact(self, body: ContactModel, user: User):
        try:
            return await self.repository.create_contact(body, user)
        except IntegrityError:
            await self.repository.db.rollback()
            _handle_integrity_error()

    async def get_contacts(
        self, name: str, email: str, skip: int, limit: int, user: User
    ):
        return await self.repository.get_contacts(name, email, skip, limit, user)

    async def get_contact(self, tag_id: int, user: User):
        return await self.repository.get_contact_by_id(tag_id, user)

    async def update_contact(self, tag_id: int, body: ContactModel, user: User):
        try:
            return await self.repository.update_contact(tag_id, body, user)
        except IntegrityError:
            await self.repository.db.rollback()
            _handle_integrity_error()

    async def remove_contact(self, tag_id: int, user: User):
        return await self.repository.remove_contact(tag_id, user)

    async def get_birthdays(self, user: User):
        return await self.repository.get_birthdays(user)
