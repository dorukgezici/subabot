import {
  createFeed,
  createKeyword,
  deleteFeed,
  deleteKeyword,
} from "@/lib/api";
import { defineAction, z } from "astro:actions";

export const server = {
  addFeed: defineAction({
    accept: "form",
    input: z.object({
      feed: z.string().url(),
    }),
    handler: async ({ feed }) => {
      await createFeed(fetch, feed);
      return { success: true };
    },
  }),
  removeFeed: defineAction({
    accept: "form",
    input: z.object({
      key: z.string(),
    }),
    handler: async ({ key }) => {
      await deleteFeed(fetch, key);
      return { success: true };
    },
  }),

  addKeyword: defineAction({
    accept: "form",
    input: z.object({
      keyword: z.string().min(3).max(30),
    }),
    handler: async ({ keyword }) => {
      await createKeyword(fetch, keyword);
      return { success: true };
    },
  }),
  removeKeyword: defineAction({
    accept: "form",
    input: z.object({
      key: z.string(),
    }),
    handler: async ({ key }) => {
      await deleteKeyword(fetch, key);
      return { success: true };
    },
  }),
};
