import dotenv from "dotenv";
import os from "os";
import app from "./app.js";
import { testConnection } from "./config/db.js";

dotenv.config();

const port = Number(process.env.PORT || 5000);

const getNetworkUrls = (serverPort) => {
  const interfaces = os.networkInterfaces();
  const urls = [];

  Object.values(interfaces).forEach((list) => {
    (list || []).forEach((entry) => {
      if (entry.family === "IPv4" && !entry.internal) {
        urls.push(`http://${entry.address}:${serverPort}`);
      }
    });
  });

  return [...new Set(urls)];
};

const startServer = async () => {
  try {
    await testConnection();
    app.listen(port, "0.0.0.0", () => {
      console.log(`Smart Campus AI backend running on port ${port}`);
      console.log(`  Local: http://localhost:${port}`);
      getNetworkUrls(port).forEach((url) => {
        console.log(`  Network: ${url}`);
      });
    });
  } catch (error) {
    console.error("Failed to start backend:", error.message);
    process.exit(1);
  }
};

startServer();