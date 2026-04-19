"""Tests for ActionReceiptStore — immutable execution receipt persistence."""

import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.action_receipt_store import ActionReceiptStore, ExecutionReceipt, ReceiptStatus


class TestReceiptCreation:
    """Receipt store creates and returns receipts with all required fields."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = ActionReceiptStore(db_path=os.path.join(self.temp_dir, "receipts.db"))

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_receipt_creates_immutable_entry(self):
        receipt = self.store.write(
            action="read configuration",
            interpreted_plan="Read app config settings",
            executed_steps=["Opened config file"],
            actor="voice",
            channel="handsfree",
            provider="claude-code",
        )
        assert isinstance(receipt, ExecutionReceipt)
        assert receipt.request_id is not None
        assert receipt.action == "read configuration"
        assert receipt.status == ReceiptStatus.COMPLETED
        assert receipt.blocked_reason is None

    def test_blocked_receipt_records_denial_reason(self):
        receipt = self.store.write(
            action="delete all files",
            interpreted_plan="",
            executed_steps=[],
            actor="voice",
            channel="handsfree",
            provider=None,
            blocked=True,
            blocked_reason="Policy POL-003: High-risk action blocked",
        )
        assert receipt.status == ReceiptStatus.BLOCKED
        assert "POL-003" in receipt.blocked_reason
        assert len(receipt.executed_steps) == 0

    def test_receipt_has_correlation_id(self):
        receipt = self.store.write(
            action="send email",
            interpreted_plan="Send email to client",
            executed_steps=["Composed email", "Sent via SMTP"],
            actor="whatsapp",
            channel="text",
            provider="claude-code",
        )
        assert receipt.correlation_id is not None
        assert len(receipt.correlation_id) > 10

    def test_receipt_includes_timestamp(self):
        receipt = self.store.write(
            action="analyze data",
            interpreted_plan="Run data analysis",
            executed_steps=["Queried DB", "Generated report"],
            actor="voice",
            channel="handsfree",
            provider="claude-code",
        )
        assert receipt.timestamp is not None
        assert len(receipt.timestamp) > 0

    def test_store_persists_across_instances(self):
        db_path = os.path.join(self.temp_dir, "persist.db")
        store1 = ActionReceiptStore(db_path=db_path)
        store1.write(
            action="test action",
            interpreted_plan="test",
            executed_steps=["step 1"],
            actor="test",
            channel="test",
            provider="test",
        )
        store2 = ActionReceiptStore(db_path=db_path)
        receipts = store2.list_all()
        assert len(receipts) == 1
        assert receipts[0].action == "test action"


class TestReceiptRetrieval:
    """Receipt store supports lookup and listing."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = ActionReceiptStore(db_path=os.path.join(self.temp_dir, "receipts.db"))

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_lookup_by_request_id(self):
        receipt = self.store.write(
            action="find user by id",
            interpreted_plan="Search user DB",
            executed_steps=["Queried users table"],
            actor="text",
            channel="whatsapp",
            provider="claude-code",
        )
        found = self.store.lookup(receipt.request_id)
        assert found is not None
        assert found.action == receipt.action

    def test_list_all_returns_chronological_receipts(self):
        self.store.write("action one", "plan 1", ["step"], "actor", "ch", "provider")
        self.store.write("action two", "plan 2", ["step"], "actor", "ch", "provider")
        self.store.write("action three", "plan 3", ["step"], "actor", "ch", "provider")

        all_receipts = self.store.list_all()
        assert len(all_receipts) == 3
        assert all_receipts[0].action == "action one"
        assert all_receipts[2].action == "action three"

    def test_list_by_status_filters_correctly(self):
        self.store.write("ok action", "plan", ["step"], "actor", "ch", "provider", blocked=False)
        self.store.write("bad action", "plan", [], "actor", "ch", None, blocked=True, blocked_reason="POL-002")

        blocked = self.store.list_by_status(ReceiptStatus.BLOCKED)
        completed = self.store.list_by_status(ReceiptStatus.COMPLETED)

        assert len(blocked) == 1
        assert len(completed) == 1
