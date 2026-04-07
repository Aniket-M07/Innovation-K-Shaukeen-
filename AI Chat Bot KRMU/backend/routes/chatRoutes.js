import { Router } from "express";
import { createChatMessage, getChatHistory, submitFeedback } from "../controllers/chatController.js";
import { protect } from "../middleware/authMiddleware.js";

const router = Router();

router.post("/", protect, createChatMessage);
router.get("/history", protect, getChatHistory);
router.post("/:chatId/feedback", protect, submitFeedback);

export default router;