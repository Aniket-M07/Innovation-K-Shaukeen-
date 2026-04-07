import { query } from "../config/db.js";

export const createDocument = async ({
  originalName,
  storedName,
  mimeType,
  size,
  path,
  uploadedBy,
}) => {
  const result = await query(
    "INSERT INTO documents (original_name, stored_name, mime_type, size, path, uploaded_by) VALUES (?, ?, ?, ?, ?, ?)",
    [originalName, storedName, mimeType, size, path, uploadedBy]
  );

  const rows = await query(
    "SELECT id, original_name, stored_name, mime_type, size, path, uploaded_by, created_at FROM documents WHERE id = ?",
    [result.insertId]
  );

  return rows[0] || null;
};

export const getDocuments = async () => {
  return query(
    `SELECT d.id, d.original_name, d.stored_name, d.mime_type, d.size, d.path, d.uploaded_by, d.created_at, u.name AS uploaded_by_name
     FROM documents d
     LEFT JOIN users u ON u.id = d.uploaded_by
     ORDER BY d.created_at DESC`
  );
};

export const getDocumentById = async (id) => {
  const rows = await query("SELECT id, original_name, stored_name, path FROM documents WHERE id = ? LIMIT 1", [id]);
  return rows[0] || null;
};

export const deleteDocumentById = async (id) => {
  const result = await query("DELETE FROM documents WHERE id = ?", [id]);
  return result.affectedRows > 0;
};

export const countDocuments = async () => {
  const rows = await query("SELECT COUNT(*) AS total FROM documents");
  return Number(rows[0].total || 0);
};