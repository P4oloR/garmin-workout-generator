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

CREATE TABLE IF NOT EXISTS public_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER,
    public_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'published',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY(creator_id) REFERENCES creators(id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_public_plans_public_id
ON public_plans(public_id);

CREATE TABLE IF NOT EXISTS plan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    day_offset INTEGER NOT NULL CHECK(day_offset BETWEEN 0 AND 6),
    display_order INTEGER NOT NULL,
    workout_snapshot TEXT NOT NULL,
    FOREIGN KEY(plan_id) REFERENCES public_plans(id) ON DELETE CASCADE,
    UNIQUE(plan_id, item_id)
);

CREATE INDEX IF NOT EXISTS idx_plan_items_plan_id
ON plan_items(plan_id);

CREATE TABLE IF NOT EXISTS athlete_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    intervals_athlete_id TEXT,
    access_token_encrypted TEXT,
    granted_scopes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_states (
    state TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    public_id TEXT NOT NULL,
    week_start TEXT NOT NULL,
    destination TEXT NOT NULL,
    created_at TEXT NOT NULL
);
