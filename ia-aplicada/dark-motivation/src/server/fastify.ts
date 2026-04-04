import Fastify from "fastify";
import { HumanMessage } from "@langchain/core/messages";
import { createGraph } from "../agent/factory.ts";

const graph = createGraph();

export const buildServer = () => {
  const server = Fastify();

  server.route({
    method: "POST",
    url: "/chat",
    schema: {
      body: {
        type: "object",
        properties: {
          message: { type: "string" },
        },
        required: ["message"],
      },
    },
    handler: async (request: any, reply: any) => {
      try {
        const result = await graph.invoke({
          messages: [new HumanMessage({ content: request.query.message })],
        });
        reply.send(result);
      } catch (error) {
        console.error(error);
        reply.status(500).send({ error: "Internal server error" });
      }
    },
  });
  return server;
};
