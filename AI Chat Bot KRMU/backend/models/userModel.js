import { query } from "../config/db.js";

export const findUserByEmail = async (email) => {
  const rows = await query("SELECT id, name, email, password, role, created_at FROM users WHERE email = ? LIMIT 1", [email]);
  return rows[0] || null;
};

export const createUser = async ({ name, email, passwordHash, role }) => {
  const result = await query(
    "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
    [name, email, passwordHash, role]
  );

  const rows = await query("SELECT id, name, email, role, created_at FROM users WHERE id = ?", [result.insertId]);
  return rows[0] || null;
};

export const countUsers = async () => {
  const rows = await query("SELECT COUNT(*) AS total FROM users");
  return Number(rows[0].total || 0);
};