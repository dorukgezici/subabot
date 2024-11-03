import {
  createFeed,
  createKeyword,
  deleteFeed,
  deleteKeyword,
} from "@/lib/api";
import { defineAction } from "astro:actions";
import { z } from "astro:schema";

export const server = {
  addFeed: defineAction({
    accept: "form",
    input: z.object({
      feed: z.string().url(),
    }),
    handler: async ({ feed }) => {
      await createFeed(feed);
      return { success: true };
    },
  }),
  removeFeed: defineAction({
    accept: "form",
    input: z.object({
      key: z.string(),
    }),
    handler: async ({ key }) => {
      await deleteFeed(key);
      return { success: true };
    },
  }),

  addKeyword: defineAction({
    accept: "form",
    input: z.object({
      keyword: z.string().min(3).max(30),
    }),
    handler: async ({ keyword }) => {
      await createKeyword(keyword);
      return { success: true };
    },
  }),
  removeKeyword: defineAction({
    accept: "form",
    input: z.object({
      key: z.string(),
    }),
    handler: async ({ key }) => {
      await deleteKeyword(key);
      return { success: true };
    },
  }),
};
