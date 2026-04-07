import { query } from "../config/db.js";

export const createChat = async ({ userId, userMessage, aiResponse }) => {
  const result = await query(
    "INSERT INTO chats (user_id, user_message, ai_response) VALUES (?, ?, ?)",
    [userId, userMessage, aiResponse]
  );

  const rows = await query(
    "SELECT id, user_id, user_message, ai_response, created_at FROM chats WHERE id = ?",
    [result.insertId]
  );

  return rows[0] || null;
};

export const getChatHistoryByUser = async (userId, limit = 50) => {
  const safeLimit = Math.max(1, Math.min(200, Number(limit) || 50));
  return query(
    `SELECT id, user_message, ai_response, created_at FROM chats WHERE user_id = ? ORDER BY created_at DESC LIMIT ${safeLimit}`,
    [userId]
  );
};

export const countChats = async () => {
  const rows = await query("SELECT COUNT(*) AS total FROM chats");
  return Number(rows[0].total || 0);
};