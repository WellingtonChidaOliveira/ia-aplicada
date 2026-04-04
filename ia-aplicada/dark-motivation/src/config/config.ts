export type ModelConfig = {
  apiKey: string;
  provider: {
    sort: {
      by: string;
      partition: string;
    };
  };
  models: string[];
};

console.assert(
  process.env.OPENROUTER_API_KEY,
  "OPENROUTER_API_KEY is not set in environment variables",
);

export const config: ModelConfig = {
  apiKey: process.env.OPENROUTER_API_KEY || "",
  models: ["cognitivecomputations/dolphin-mistral-24b-venice-edition:free"],
  provider: {
    sort: {
      by: "price",
      partition: "none",
    },
  },
};
