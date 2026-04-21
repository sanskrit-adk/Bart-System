"""
BART Transportation System — SQLite Persistence Layer
Stores users, cards, transactions, and trips across sessions.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "bart.db"


class Database:
    def __init__(self, in_memory: bool = False):
        """
        in_memory=True  → temporary :memory: DB (used by tests)
        in_memory=False → persistent file DB (production)
        """
        if in_memory:
            self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     TEXT PRIMARY KEY,
                username    TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email       TEXT NOT NULL,
                role        TEXT NOT NULL,
                name        TEXT NOT NULL,
                passenger_type TEXT,
                department  TEXT,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cards (
                card_id     TEXT PRIMARY KEY,
                owner_id    TEXT NOT NULL,
                balance     REAL NOT NULL DEFAULT 0.0,
                status      TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at  TEXT NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS transactions (
                tx_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id     TEXT NOT NULL,
                tx_type     TEXT NOT NULL,
                amount      REAL NOT NULL,
                balance_after REAL NOT NULL,
                description TEXT,
                timestamp   TEXT NOT NULL,
                FOREIGN KEY (card_id) REFERENCES cards(card_id)
            );

            CREATE TABLE IF NOT EXISTS trips (
                trip_id         TEXT PRIMARY KEY,
                card_id         TEXT NOT NULL,
                passenger_id    TEXT NOT NULL,
                entry_station   TEXT NOT NULL,
                exit_station    TEXT,
                start_time      TEXT NOT NULL,
                end_time        TEXT,
                fare            REAL,
                status          TEXT NOT NULL DEFAULT 'ACTIVE',
                FOREIGN KEY (card_id) REFERENCES cards(card_id),
                FOREIGN KEY (passenger_id) REFERENCES users(user_id)
            );
        """)
        self.conn.commit()

    # ── Users ─────────────────────────────────────────────────────────────────

    def save_user(self, user) -> None:
        """Insert or update a user row."""
        from .models import Passenger, Admin, SuperAdmin
        passenger_type = None
        department = None
        if isinstance(user, Passenger):
            passenger_type = user.passenger_type.name
        elif isinstance(user, Admin):
            department = getattr(user, 'department', 'Operations')

        self.conn.execute("""
            INSERT OR REPLACE INTO users
                (user_id, username, password_hash, email, role,
                 name, passenger_type, department, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.user_id, user.username, user.password_hash,
            user.email, user.role.name,
            getattr(user, 'name', user.username),
            passenger_type, department,
            user.created_at.isoformat()
        ))
        self.conn.commit()

    def load_users(self) -> list:
        """Return all user rows as sqlite3.Row objects."""
        return self.conn.execute("SELECT * FROM users").fetchall()

    def update_user(self, user) -> None:
        """Persist name / passenger_type / department changes."""
        from .models import Passenger, Admin
        passenger_type = None
        department = None
        if isinstance(user, Passenger):
            passenger_type = user.passenger_type.name
        elif isinstance(user, Admin):
            department = getattr(user, 'department', 'Operations')

        self.conn.execute("""
            UPDATE users
               SET name=?, passenger_type=?, department=?, password_hash=?
             WHERE user_id=?
        """, (
            getattr(user, 'name', user.username),
            passenger_type, department,
            user.password_hash,
            user.user_id
        ))
        self.conn.commit()

    # ── Cards ─────────────────────────────────────────────────────────────────

    def save_card(self, card, owner_id: str) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO cards
                (card_id, owner_id, balance, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            card.card_id, owner_id,
            card.balance, card.status.name,
            datetime.now().isoformat()
        ))
        self.conn.commit()

    def update_card(self, card) -> None:
        self.conn.execute("""
            UPDATE cards SET balance=?, status=? WHERE card_id=?
        """, (card.balance, card.status.name, card.card_id))
        self.conn.commit()

    def load_cards(self) -> list:
        return self.conn.execute("SELECT * FROM cards").fetchall()

    # ── Transactions ──────────────────────────────────────────────────────────

    def save_transaction(self, card_id: str, tx_type: str,
                         amount: float, balance_after: float,
                         description: str = "") -> None:
        self.conn.execute("""
            INSERT INTO transactions
                (card_id, tx_type, amount, balance_after, description, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (card_id, tx_type, amount, balance_after,
              description, datetime.now().isoformat()))
        self.conn.commit()

    def load_transactions(self, card_id: str) -> list:
        return self.conn.execute("""
            SELECT * FROM transactions WHERE card_id=? ORDER BY timestamp
        """, (card_id,)).fetchall()

    # ── Trips ─────────────────────────────────────────────────────────────────

    def save_trip(self, trip) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO trips
                (trip_id, card_id, passenger_id,
                 entry_station, exit_station,
                 start_time, end_time, fare, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trip.trip_id,
            trip.card.card_id,
            trip.passenger.user_id,
            trip.entry_station.station_id,
            trip.exit_station.station_id if trip.exit_station else None,
            trip.start_time.isoformat(),
            trip.end_time.isoformat() if trip.end_time else None,
            trip.fare,
            trip.status.name
        ))
        self.conn.commit()

    def load_trips(self) -> list:
        return self.conn.execute("SELECT * FROM trips ORDER BY start_time").fetchall()

    def close(self) -> None:
        self.conn.close()
