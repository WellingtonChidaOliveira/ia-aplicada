import Fastify from "fastify";
import { chatRoutes } from "./routes/chatRoutes.ts";
import { loadConfig } from "../config/config.ts";

export const startServer = async () => {
  const cfg = loadConfig();
  try {
    const app = Fastify();
    await app.register(chatRoutes);

    await app.listen({ port: cfg.port, host: "0.0.0.0" });
    console.log(`Server started on port ${cfg.port}`);
  } catch (error) {
    console.error("Error starting server", error);
    process.exit(1);
  }
};
