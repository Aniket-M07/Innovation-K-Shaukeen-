import { query } from "../config/db.js";

export const createFeedback = async ({ chatId, userId, rating, comment }) => {
  const result = await query(
    "INSERT INTO feedback (chat_id, user_id, rating, comment) VALUES (?, ?, ?, ?)",
    [chatId, userId, rating, comment || null]
  );

  const rows = await query("SELECT id, chat_id, user_id, rating, comment, created_at FROM feedback WHERE id = ?", [
    result.insertId,
  ]);

  return rows[0] || null;
};

export const countFeedback = async () => {
  const rows = await query("SELECT COUNT(*) AS total FROM feedback");
  return Number(rows[0].total || 0);
};

export const getRecentFeedbackContext = async (limit = 10) => {
  const safeLimit = Math.max(1, Math.min(50, Number(limit) || 10));
  return query(
    `SELECT rating, comment, created_at
     FROM feedback
     ORDER BY created_at DESC
     LIMIT ${safeLimit}`
  );
};