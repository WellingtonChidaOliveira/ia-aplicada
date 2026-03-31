import { OpenRouter } from "@openrouter/sdk";
import type { Config } from "../../config/config.ts";
import type { ChatResponse } from "@openrouter/sdk/models";

let openRouterClient: OpenRouter | null = null;

export const responseModel = async (
  question: string,
  cfg: Config,
): Promise<ChatResponse> => {
  if (!openRouterClient) {
    openRouterClient = new OpenRouter({
      apiKey: cfg.openRouterApiKey,
    });
  }

  const resp = await openRouterClient.chat.send({
    models: cfg.models,
    messages: [
      {
        role: "system",
        content: "You are a helpful assistant.",
      },
      {
        role: "user",
        content: question,
      },
    ],
    provider: {
      sort: {
        by: "price",
        partition: "none",
      },
    },
    stream: false,
  });

  return resp;
};
