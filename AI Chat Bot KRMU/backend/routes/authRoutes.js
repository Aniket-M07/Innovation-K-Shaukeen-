import { Router } from "express";
import { login, register, createAdmin } from "../controllers/authController.js";
import { protect, authorizeRoles } from "../middleware/authMiddleware.js";

const router = Router();

router.post("/register", register);
router.post("/login", login);
router.post("/create-admin", protect, authorizeRoles("admin"), createAdmin);

export default router;