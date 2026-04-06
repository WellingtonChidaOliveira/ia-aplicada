import { AIMessage } from "@langchain/core/messages";
import { type GraphMessageState } from "../graph.ts";
import { LlmRouterService } from "../../server/llmRouterService.ts";
import {
  systemCommandPrompt,
  systemCommandSchema,
  systemPromptInstructions,
} from "../../prompts/v1/systemCommand.ts";

export function phraseGenerator(llmClient: LlmRouterService) {
  return async (
    state: GraphMessageState,
  ): Promise<Partial<GraphMessageState>> => {
    const result = await llmClient.generateStructed(
      systemCommandPrompt(),
      systemPromptInstructions(),
      systemCommandSchema,
    );

    if (!result.success) {
      return {
        success: false,
        failed: true,
        error: result.error,
      };
    }

    return {
      ...state,
      messages: [
        ...state.messages,
        new AIMessage({ content: result.data?.message }),
      ],
      success: true,
    };
  };
}
