import fs from "fs/promises";
import path from "path";
import {
  createDocument,
  deleteDocumentById,
  getDocumentById,
  getDocuments,
  countDocuments,
} from "../models/documentModel.js";
import { countChats } from "../models/chatModel.js";
import { countUsers } from "../models/userModel.js";
import { countFeedback } from "../models/feedbackModel.js";
import { embedFileWithAIEngine } from "../services/aiEngineService.js";

export const uploadDocument = async (req, res, next) => {
  try {
    if (!req.file) {
      return res.status(400).json({ message: "file is required" });
    }

    let embedResult;
    try {
      embedResult = await embedFileWithAIEngine(req.file);
    } catch (error) {
      const absolutePath = path.resolve(req.file.path);
      await fs.unlink(absolutePath).catch(() => undefined);
      return res.status(502).json({
        message: "Document upload failed during AI embedding",
        error: error.message,
      });
    }

    const saved = await createDocument({
      originalName: req.file.originalname,
      storedName: req.file.filename,
      mimeType: req.file.mimetype,
      size: req.file.size,
      path: req.file.path,
      uploadedBy: req.user.id,
    });

    return res.status(201).json({
      message: "Document uploaded",
      data: {
        ...saved,
        embedding: embedResult,
      },
    });
  } catch (error) {
    return next(error);
  }
};

export const listDocuments = async (req, res, next) => {
  try {
    const docs = await getDocuments();
    return res.json({ message: "Documents fetched", data: docs });
  } catch (error) {
    return next(error);
  }
};

export const removeDocument = async (req, res, next) => {
  try {
    const id = Number(req.params.id);
    if (!id) {
      return res.status(400).json({ message: "valid document id is required" });
    }

    const doc = await getDocumentById(id);
    if (!doc) {
      return res.status(404).json({ message: "Document not found" });
    }

    const deleted = await deleteDocumentById(id);

    if (deleted && doc.path) {
      const absolutePath = path.resolve(doc.path);
      await fs.unlink(absolutePath).catch(() => undefined);
    }

    return res.json({ message: "Document deleted" });
  } catch (error) {
    return next(error);
  }
};

export const getAnalytics = async (req, res, next) => {
  try {
    const [totalUsers, totalChats, totalDocuments, totalFeedback] = await Promise.all([
      countUsers(),
      countChats(),
      countDocuments(),
      countFeedback(),
    ]);

    return res.json({
      message: "Analytics fetched",
      data: {
        totalUsers,
        totalChats,
        totalDocuments,
        totalFeedback,
      },
    });
  } catch (error) {
    return next(error);
  }
};