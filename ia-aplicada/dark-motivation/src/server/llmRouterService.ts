import { ChatOpenAI } from "@langchain/openai";
import { config, type ModelConfig } from "../config/config.ts";
import { z } from "zod/v3";
import {
  createAgent,
  HumanMessage,
  providerStrategy,
  SystemMessage,
} from "langchain";

export class LlmRouterService {
  private config: ModelConfig;
  private llmClient: ChatOpenAI;

  constructor(cfg: ModelConfig) {
    this.config = cfg ?? config;

    this.llmClient = new ChatOpenAI({
      apiKey: this.config.apiKey,
      modelName: this.config.models.at(0),
      temperature: 0.7,
      configuration: {
        baseURL: "https://openrouter.ai/api/v1",
      },
      modelKwargs: {
        models: this.config.models,
        provider: this.config.provider,
      },
    });
  }

  async generateStructed<T>(
    systemPrompt: string,
    userPrompt: string,
    schema: z.ZodType<T>,
  ) {
    try {
      const agent = createAgent({
        model: this.llmClient,
        tools: [],
        responseFormat: providerStrategy(schema),
      });
      const messages = [
        new SystemMessage(systemPrompt),
        new HumanMessage(userPrompt),
      ];
      const data = await agent.invoke({ messages });
      return {
        success: true,
        data: data.structuredResponse,
      };
    } catch (error) {
      console.log("Error generating structured response:", error);
      return {
        success: false,
        failed: true,
        error: error instanceof Error ? error.message : String(error),
        data: null,
      };
    }
  }
}
