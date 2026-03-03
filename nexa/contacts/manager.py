"""
Nexa AI — Contact Manager
Load, save, search, add, update, and delete contacts from contacts.json.
"""

import json
from pathlib import Path
from typing import Any, Optional

from nexa.utils.logger import get_logger

logger = get_logger(__name__)

# Default contacts file lives alongside this module
_DEFAULT_FILE = Path(__file__).parent / "contacts.json"


class ContactManager:
    """
    Manages a simple JSON-based contact book.

    Each contact entry structure:
    {
        "phone": "+91XXXXXXXXXX",
        "relation": "friend",
        "platforms": ["phone", "whatsapp", "messenger"]
    }
    """

    def __init__(self, filepath: Optional[str] = None) -> None:
        self._filepath = Path(filepath) if filepath else _DEFAULT_FILE
        self._contacts: dict[str, dict[str, Any]] = {}
        self.load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load contacts from the JSON file."""
        try:
            if self._filepath.exists():
                with open(self._filepath, "r", encoding="utf-8") as f:
                    self._contacts = json.load(f)
                logger.info(f"📒 Loaded {len(self._contacts)} contact(s) from {self._filepath}")
            else:
                self._contacts = {}
        except Exception as exc:
            logger.error(f"load contacts error: {exc}")
            self._contacts = {}

    def save(self) -> None:
        """Persist contacts to the JSON file."""
        try:
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump(self._contacts, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.error(f"save contacts error: {exc}")

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_contact(
        self,
        name: str,
        phone: str,
        relation: str = "friend",
        platforms: Optional[list[str]] = None,
    ) -> bool:
        """
        Add or update a contact.

        Args:
            name: Contact display name (used as key).
            phone: Phone number in international format.
            relation: Relationship label (e.g. "friend", "family").
            platforms: List of platforms (e.g. ["phone", "whatsapp"]).

        Returns:
            True always (upsert semantics).
        """
        self._contacts[name] = {
            "phone": phone,
            "relation": relation,
            "platforms": platforms or ["phone"],
        }
        self.save()
        logger.info(f"✅ Contact saved: {name} ({phone})")
        return True

    def get_contact(self, name: str) -> Optional[dict[str, Any]]:
        """
        Retrieve a contact by name (fuzzy, case-insensitive).

        Args:
            name: Name or partial name to search for.

        Returns:
            Contact dict with an added "name" key, or None if not found.
        """
        name_lower = name.lower()

        # Exact match first
        for key, data in self._contacts.items():
            if key.lower() == name_lower:
                return {"name": key, **data}

        # Partial / fuzzy match
        for key, data in self._contacts.items():
            if name_lower in key.lower() or key.lower() in name_lower:
                return {"name": key, **data}

        logger.warning(f"Contact not found: '{name}'")
        return None

    def delete_contact(self, name: str) -> bool:
        """
        Remove a contact by name.

        Args:
            name: Exact or fuzzy name to remove.

        Returns:
            True if a contact was deleted.
        """
        contact = self.get_contact(name)
        if not contact:
            return False
        del self._contacts[contact["name"]]
        self.save()
        logger.info(f"🗑️  Contact deleted: {contact['name']}")
        return True

    def list_contacts(self) -> list[dict[str, Any]]:
        """Return all contacts as a list of dicts (each with a "name" key)."""
        return [{"name": k, **v} for k, v in sorted(self._contacts.items())]

    def update_contact(self, name: str, **kwargs: Any) -> bool:
        """
        Update fields of an existing contact.

        Args:
            name: Contact name to update.
            **kwargs: Fields to update (phone, relation, platforms).

        Returns:
            True if updated, False if contact not found.
        """
        contact = self.get_contact(name)
        if not contact:
            return False
        key = contact["name"]
        for field, value in kwargs.items():
            self._contacts[key][field] = value
        self.save()
        logger.info(f"✏️  Contact updated: {key}")
        return True


# Module-level singleton
contact_manager = ContactManager()
