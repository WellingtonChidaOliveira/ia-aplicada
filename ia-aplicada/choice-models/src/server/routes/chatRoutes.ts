import type { FastifyInstance } from "fastify";
import { responseModel } from "../../service/OpenRouter/operRouterService.ts";
import { loadConfig } from "../../config/config.ts";

type ChatRequest = {
  Body: {
    question: string;
  };
};

const cfg = loadConfig();

export const chatRoutes = (server: FastifyInstance) => {
  server.post<ChatRequest>(
    "/chat",
    {
      schema: {
        body: {
          type: "object",
          required: ["question"],
          properties: {
            question: {
              type: "string",
            },
          },
        },
      },
    },
    async (req, reply) => {
      try {
        const { question } = req.body;
        const resp = await responseModel(question, cfg);
        reply.status(200).send({
          model: resp.model,
          response: resp.choices[0].message.content,
        });
      } catch (error) {
        console.error("Error on /chat", error);
        reply.status(500).send({ error: "Ocorreu um erro interno ao processar a requisição." });
      }
    },
  );
};
