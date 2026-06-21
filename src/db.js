// Слой работы с базой данных SQLite (better-sqlite3 — синхронный, без колбэков).

const fs = require("fs");
const path = require("path");
const Database = require("better-sqlite3");

const { dbPath } = require("./config");

// Создаём каталог под БД, если его ещё нет.
const dir = path.dirname(dbPath);
if (dir && !fs.existsSync(dir)) {
  fs.mkdirSync(dir, { recursive: true });
}

const db = new Database(dbPath);
db.pragma("journal_mode = WAL");

db.exec(`
  CREATE TABLE IF NOT EXISTS tickets (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    username     TEXT,
    contact_name TEXT,
    category     TEXT NOT NULL,
    location     TEXT NOT NULL,
    description  TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'new',
    assigned_to  INTEGER,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
  );

  CREATE INDEX IF NOT EXISTS idx_tickets_user   ON tickets(user_id);
  CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);

  CREATE TABLE IF NOT EXISTS comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id  INTEGER NOT NULL,
    author_id  INTEGER NOT NULL,
    text       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
  );
`);

module.exports = db;
