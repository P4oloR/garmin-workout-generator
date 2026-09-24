PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS creators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    revoked_at TEXT
);

CREATE TABLE IF NOT EXISTS creator_pairings (
    pairing_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    token_encrypted TEXT,
    creator_id INTEGER,
    created_at TEXT NOT NULL,
    approved_at TEXT,
    consumed_at TEXT,
    FOREIGN KEY(creator_id) REFERENCES creators(id) ON DELETE SET NULL
);

ALTER TABLE public_plans ADD COLUMN creator_id INTEGER REFERENCES creators(id);
