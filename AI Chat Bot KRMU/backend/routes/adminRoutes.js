import { Router } from "express";
import {
  uploadDocument,
  listDocuments,
  removeDocument,
  getAnalytics,
} from "../controllers/adminController.js";
import { authorizeRoles, protect } from "../middleware/authMiddleware.js";
import upload from "../middleware/uploadMiddleware.js";

const router = Router();

router.post("/upload", protect, authorizeRoles("admin"), upload.single("file"), uploadDocument);
router.get("/documents", protect, authorizeRoles("admin"), listDocuments);
router.delete("/document/:id", protect, authorizeRoles("admin"), removeDocument);
router.get("/analytics", protect, authorizeRoles("admin"), getAnalytics);

export default router;