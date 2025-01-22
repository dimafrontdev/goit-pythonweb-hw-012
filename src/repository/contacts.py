from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import or_
from sqlalchemy import func

from src.database.models import Contact, User
from src.schemas import ContactModel

from datetime import datetime, timedelta


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(
        self, name: str, email: str, skip: int, limit: int, user: User
    ) -> List[Contact]:
        stmt = (
            select(Contact)
            .filter_by(user=user)
            .where(
                or_(Contact.first_name.contains(name), Contact.last_name.contains(name))
            )
            .where(Contact.email.contains(email))
            .offset(skip)
            .limit(limit)
        )
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact:
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactModel, user: User
    ) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            if contact:
                for key, value in body.dict(exclude_unset=True).items():
                    setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def get_birthdays(self, user: User) -> list[Contact]:
        today = datetime.now().date()
        week = today + timedelta(days=7)

        stmt = select(Contact).where(
            Contact.user == user,
            or_(
                func.to_char(Contact.birthday, "MM-DD").between(
                    today.strftime("%m-%d"), week.strftime("%m-%d")
                )
            ),
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
