import "dotenv/config";
import bcrypt from "bcryptjs";
import { query } from "../config/db.js";

const args = process.argv.slice(2);
const command = args[0];

const getOption = (name) => {
  const index = args.indexOf(`--${name}`);
  if (index === -1 || index + 1 >= args.length) {
    return "";
  }
  return String(args[index + 1]).trim();
};

const printUsage = () => {
  console.log("Admin Tools Usage:");
  console.log("  node backend/scripts/adminTools.js list");
  console.log("  node backend/scripts/adminTools.js create --name \"Admin Name\" --email admin@example.com --password \"StrongPass123\"");
  console.log("  node backend/scripts/adminTools.js remove --email admin@example.com");
  console.log("  node backend/scripts/adminTools.js promote --email user@example.com");
  console.log("  node backend/scripts/adminTools.js demote --email admin@example.com");
};

const listAdmins = async () => {
  const admins = await query(
    "SELECT id, name, email, role, created_at FROM users WHERE role = 'admin' ORDER BY id"
  );

  if (!admins.length) {
    console.log("No admin accounts found.");
    return;
  }

  console.table(admins);
};

const createAdmin = async () => {
  const name = getOption("name");
  const email = getOption("email");
  const password = getOption("password");

  if (!name || !email || !password) {
    throw new Error("Missing required options. Use --name, --email and --password.");
  }

  const existing = await query("SELECT id, role FROM users WHERE email = ? LIMIT 1", [email]);
  if (existing.length) {
    throw new Error("Email already exists. Use promote command if this is a student account.");
  }

  const passwordHash = await bcrypt.hash(password, 10);
  await query("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'admin')", [
    name,
    email,
    passwordHash,
  ]);

  console.log(`Admin created successfully for ${email}`);
};

const removeAdmin = async () => {
  const email = getOption("email");

  if (!email) {
    throw new Error("Missing required option --email");
  }

  const target = await query("SELECT id, role FROM users WHERE email = ? LIMIT 1", [email]);
  if (!target.length) {
    throw new Error("No user found with that email.");
  }

  if (target[0].role !== "admin") {
    throw new Error("This user is not an admin.");
  }

  const adminCountRows = await query("SELECT COUNT(*) AS total FROM users WHERE role = 'admin'");
  const adminCount = Number(adminCountRows[0]?.total || 0);

  if (adminCount <= 1) {
    throw new Error("Cannot remove the last admin account.");
  }

  await query("DELETE FROM users WHERE email = ? AND role = 'admin'", [email]);
  console.log(`Admin removed successfully for ${email}`);
};

const promoteUser = async () => {
  const email = getOption("email");

  if (!email) {
    throw new Error("Missing required option --email");
  }

  const target = await query("SELECT id, role FROM users WHERE email = ? LIMIT 1", [email]);
  if (!target.length) {
    throw new Error("No user found with that email.");
  }

  if (target[0].role === "admin") {
    console.log("User is already admin.");
    return;
  }

  await query("UPDATE users SET role = 'admin' WHERE email = ?", [email]);
  console.log(`User promoted to admin: ${email}`);
};

const demoteAdmin = async () => {
  const email = getOption("email");

  if (!email) {
    throw new Error("Missing required option --email");
  }

  const target = await query("SELECT id, role FROM users WHERE email = ? LIMIT 1", [email]);
  if (!target.length) {
    throw new Error("No user found with that email.");
  }

  if (target[0].role !== "admin") {
    console.log("User is already student.");
    return;
  }

  const adminCountRows = await query("SELECT COUNT(*) AS total FROM users WHERE role = 'admin'");
  const adminCount = Number(adminCountRows[0]?.total || 0);

  if (adminCount <= 1) {
    throw new Error("Cannot demote the last admin account.");
  }

  await query("UPDATE users SET role = 'student' WHERE email = ?", [email]);
  console.log(`Admin demoted to student: ${email}`);
};

const run = async () => {
  try {
    if (!command) {
      printUsage();
      return;
    }

    if (command === "list") {
      await listAdmins();
      return;
    }

    if (command === "create") {
      await createAdmin();
      return;
    }

    if (command === "remove") {
      await removeAdmin();
      return;
    }

    if (command === "promote") {
      await promoteUser();
      return;
    }

    if (command === "demote") {
      await demoteAdmin();
      return;
    }

    printUsage();
    process.exitCode = 1;
  } catch (error) {
    console.error(error.message || "Failed to run admin tool.");
    process.exitCode = 1;
  }
};

run();
