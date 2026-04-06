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
  models: ["nvidia/nemotron-3-super-120b-a12b:free"],
  provider: {
    sort: {
      by: "price",
      partition: "none",
    },
  },
};
