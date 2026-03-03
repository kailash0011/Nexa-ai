"""
Tests for nexa/contacts — ContactManager CRUD operations.
"""

import json
import tempfile
from pathlib import Path

import pytest

from nexa.contacts.manager import ContactManager


@pytest.fixture
def manager(tmp_path):
    """Create a fresh ContactManager backed by a temp file."""
    contacts_file = tmp_path / "contacts.json"
    contacts_file.write_text("{}")  # start empty
    return ContactManager(filepath=str(contacts_file))


class TestContactManager:
    def test_add_and_get_contact(self, manager):
        manager.add_contact("Alice", "+911234567890", relation="friend", platforms=["phone", "whatsapp"])
        contact = manager.get_contact("Alice")
        assert contact is not None
        assert contact["phone"] == "+911234567890"
        assert contact["relation"] == "friend"

    def test_get_contact_case_insensitive(self, manager):
        manager.add_contact("Bob", "+910000000001")
        assert manager.get_contact("bob") is not None
        assert manager.get_contact("BOB") is not None

    def test_get_contact_partial_match(self, manager):
        manager.add_contact("Charlie Brown", "+910000000002")
        result = manager.get_contact("Charlie")
        assert result is not None
        assert result["name"] == "Charlie Brown"

    def test_get_contact_not_found(self, manager):
        result = manager.get_contact("NonExistentPerson")
        assert result is None

    def test_list_contacts(self, manager):
        manager.add_contact("Dave", "+910000000003")
        manager.add_contact("Eve", "+910000000004")
        contacts = manager.list_contacts()
        names = [c["name"] for c in contacts]
        assert "Dave" in names
        assert "Eve" in names

    def test_list_contacts_empty(self, manager):
        contacts = manager.list_contacts()
        assert contacts == []

    def test_delete_contact(self, manager):
        manager.add_contact("Frank", "+910000000005")
        result = manager.delete_contact("Frank")
        assert result is True
        assert manager.get_contact("Frank") is None

    def test_delete_nonexistent(self, manager):
        result = manager.delete_contact("Nobody")
        assert result is False

    def test_update_contact(self, manager):
        manager.add_contact("Grace", "+910000000006")
        manager.update_contact("Grace", phone="+919999999999")
        updated = manager.get_contact("Grace")
        assert updated["phone"] == "+919999999999"

    def test_update_nonexistent(self, manager):
        result = manager.update_contact("Phantom", phone="+910000000000")
        assert result is False

    def test_persistence(self, tmp_path):
        """Contacts saved by one manager are loaded by another."""
        filepath = str(tmp_path / "contacts.json")
        m1 = ContactManager(filepath=filepath)
        m1.add_contact("Hank", "+910000000007")

        m2 = ContactManager(filepath=filepath)
        assert m2.get_contact("Hank") is not None

    def test_default_platforms(self, manager):
        manager.add_contact("Ivy", "+910000000008")
        contact = manager.get_contact("Ivy")
        assert "phone" in contact["platforms"]

    def test_contacts_json_contains_sample_contacts(self):
        """The default contacts.json should have Ram and Sandhya pre-loaded."""
        default_manager = ContactManager()  # uses bundled contacts.json
        ram = default_manager.get_contact("Ram")
        sandhya = default_manager.get_contact("Sandhya")
        assert ram is not None, "Ram should be in the default contacts"
        assert sandhya is not None, "Sandhya should be in the default contacts"
