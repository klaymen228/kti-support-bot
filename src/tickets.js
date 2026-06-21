// Сервисный слой: вся бизнес-логика заявок поверх таблиц БД.

const db = require("./db");

const ACTIVE_STATUSES = ["new", "in_progress"];

function createTicket({
  userId,
  username,
  contactName,
  category,
  location,
  description,
}) {
  const stmt = db.prepare(`
    INSERT INTO tickets (user_id, username, contact_name, category, location, description)
    VALUES (@userId, @username, @contactName, @category, @location, @description)
  `);
  const info = stmt.run({
    userId,
    username: username || null,
    contactName: contactName || null,
    category,
    location,
    description,
  });
  return getTicket(info.lastInsertRowid);
}

function getTicket(id) {
  return db.prepare("SELECT * FROM tickets WHERE id = ?").get(id);
}

function getUserTickets(userId, limit = 20) {
  return db
    .prepare(
      "SELECT * FROM tickets WHERE user_id = ? ORDER BY created_at DESC LIMIT ?"
    )
    .all(userId, limit);
}

function getActiveTickets(limit = 50) {
  const placeholders = ACTIVE_STATUSES.map(() => "?").join(",");
  return db
    .prepare(
      `SELECT * FROM tickets WHERE status IN (${placeholders})
       ORDER BY
         CASE status WHEN 'new' THEN 0 ELSE 1 END,
         created_at ASC
       LIMIT ?`
    )
    .all(...ACTIVE_STATUSES, limit);
}

function updateStatus(id, status, assignedTo = null) {
  db.prepare(
    `UPDATE tickets
       SET status = ?,
           assigned_to = COALESCE(?, assigned_to),
           updated_at = datetime('now')
     WHERE id = ?`
  ).run(status, assignedTo, id);
  return getTicket(id);
}

function addComment(ticketId, authorId, text) {
  db.prepare(
    "INSERT INTO comments (ticket_id, author_id, text) VALUES (?, ?, ?)"
  ).run(ticketId, authorId, text);
  db.prepare("UPDATE tickets SET updated_at = datetime('now') WHERE id = ?").run(
    ticketId
  );
}

function getComments(ticketId) {
  return db
    .prepare("SELECT * FROM comments WHERE ticket_id = ? ORDER BY created_at ASC")
    .all(ticketId);
}

function getStats() {
  const rows = db
    .prepare("SELECT status, COUNT(*) AS n FROM tickets GROUP BY status")
    .all();
  const stats = { new: 0, in_progress: 0, done: 0, rejected: 0, total: 0 };
  for (const r of rows) {
    stats[r.status] = r.n;
    stats.total += r.n;
  }
  return stats;
}

module.exports = {
  createTicket,
  getTicket,
  getUserTickets,
  getActiveTickets,
  updateStatus,
  addComment,
  getComments,
  getStats,
};
