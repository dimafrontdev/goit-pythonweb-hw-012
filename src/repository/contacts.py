from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import or_
from sqlalchemy import func

from src.database.models import Contact, User
from src.schemas import ContactModel

from datetime import datetime, timedelta


class ContactRepository:
    """
    Repository for managing contact-related database operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize a ContactRepository.

        Args:
            session: An AsyncSession object connected to the database.
        """
        self.db = session

    async def get_contacts(
        self, name: str, email: str, skip: int, limit: int, user: User
    ) -> List[Contact]:
        """
        Retrieve a list of contacts owned by a user, filtered by name and email with pagination.

        Args:
            name: The name filter for the contacts.
            email: The email filter for the contacts.
            skip: The number of contacts to skip.
            limit: The maximum number of contacts to return.
            user: The owner of the contacts.

        Returns:
            A list of Contact objects matching the filters.
        """
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
        """
        Retrieve a contact by its ID.

        Args:
            contact_id: The ID of the contact.
            user: The owner of the contact.

        Returns:
            The contact if found, otherwise None.
        """
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact:
        """
        Create a new contact.

        Args:
            body: A ContactModel containing contact details.
            user: The owner of the contact.

        Returns:
            The newly created Contact object.
        """
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactModel, user: User
    ) -> Contact | None:
        """
        Update an existing contact.

        Args:
            contact_id: The ID of the contact to update.
            body: A ContactModel containing updated contact details.
            user: The owner of the contact.

        Returns:
            The updated Contact object, or None if not found.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        """
        Remove a contact by its ID.

        Args:
            contact_id: The ID of the contact to remove.
            user: The owner of the contact.

        Returns:
            The deleted Contact object, or None if not found.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def get_birthdays(self, user: User) -> list[Contact]:
        """
        Retrieve contacts with upcoming birthdays within the next 7 days.

        Args:
            user: The owner of the contacts.

        Returns:
            A list of contacts whose birthdays fall within the next 7 days.
        """
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
