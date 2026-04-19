"""Action Receipt Store — immutable execution receipt persistence via SQLite."""

import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


class ReceiptStatus(Enum):
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class ExecutionReceipt:
    request_id: str
    correlation_id: str
    action: str
    interpreted_plan: str
    executed_steps: list
    status: ReceiptStatus
    actor: str
    channel: str
    provider: Optional[str]
    blocked_reason: Optional[str]
    timestamp: str


class ActionReceiptStore:
    """SQLite-backed immutable receipt storage."""

    def __init__(self, db_path: str = "memory/receipts.db"):
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    request_id TEXT PRIMARY KEY,
                    correlation_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    interpreted_plan TEXT DEFAULT '',
                    executed_steps TEXT DEFAULT '[]',
                    status TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    provider TEXT,
                    blocked_reason TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_receipts_status ON receipts(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_receipts_timestamp ON receipts(timestamp)")

    def write(
        self,
        action: str,
        interpreted_plan: str,
        executed_steps: list,
        actor: str,
        channel: str,
        provider: Optional[str] = None,
        blocked: bool = False,
        blocked_reason: Optional[str] = None,
    ) -> ExecutionReceipt:
        request_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        status = ReceiptStatus.BLOCKED if blocked else ReceiptStatus.COMPLETED
        timestamp = datetime.now().isoformat()

        receipt = ExecutionReceipt(
            request_id=request_id,
            correlation_id=correlation_id,
            action=action,
            interpreted_plan=interpreted_plan,
            executed_steps=executed_steps,
            status=status,
            actor=actor,
            channel=channel,
            provider=provider,
            blocked_reason=blocked_reason,
            timestamp=timestamp,
        )

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """INSERT INTO receipts VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    request_id,
                    correlation_id,
                    action,
                    interpreted_plan,
                    json.dumps(executed_steps),
                    status.value,
                    actor,
                    channel,
                    provider,
                    blocked_reason,
                    timestamp,
                ),
            )

        logger.info(f"🧾 Receipt written: {request_id} status={status.value}")
        return receipt

    def lookup(self, request_id: str) -> Optional[ExecutionReceipt]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM receipts WHERE request_id = ?", (request_id,)
            ).fetchone()

        if row is None:
            return None

        return self._row_to_receipt(row)

    def list_all(self) -> List[ExecutionReceipt]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM receipts ORDER BY timestamp ASC"
            ).fetchall()
        return [self._row_to_receipt(r) for r in rows]

    def list_by_status(self, status: ReceiptStatus) -> List[ExecutionReceipt]:
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM receipts WHERE status = ? ORDER BY timestamp ASC",
                (status.value,),
            ).fetchall()
        return [self._row_to_receipt(r) for r in rows]

    @staticmethod
    def _row_to_receipt(row) -> ExecutionReceipt:
        return ExecutionReceipt(
            request_id=row["request_id"],
            correlation_id=row["correlation_id"],
            action=row["action"],
            interpreted_plan=row["interpreted_plan"],
            executed_steps=json.loads(row["executed_steps"] or "[]"),
            status=ReceiptStatus(row["status"]),
            actor=row["actor"],
            channel=row["channel"],
            provider=row["provider"],
            blocked_reason=row["blocked_reason"],
            timestamp=row["timestamp"],
        )
