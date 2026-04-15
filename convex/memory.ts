import { v } from "convex/values";
import { action, mutation, query } from "./_generated/server";

/**
 * Perform a vector search for semantically similar past research.
 * Must be an 'action' as vectorSearch is only available in actions.
 */
export const search = action({
  args: {
    embedding: v.array(v.number()),
    topK: v.number(),
  },
  handler: async (ctx, args) => {
    // Perform the vector search
    const results = await ctx.vectorSearch("research_memory", "by_embedding", {
      vector: args.embedding,
      limit: args.topK,
    });

    // Return the matched contents
    const matches = await Promise.all(
      results.map(async (r) => {
        const doc = await ctx.runQuery("memory:internalGet", { id: r._id });
        return {
           content: doc.content,
           quality_score: doc.quality_score,
           ttl_expires: doc.ttl_expires
        };
      })
    );

    return matches;
  },
});

/**
 * Internal query to fetch a full document by ID (required for actions to fetch data).
 */
export const internalGet = query({
  args: { id: v.id("research_memory") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

/**
 * Store new research findings into the vector index.
 */
export const store = mutation({
  args: {
    content: v.string(),
    embedding: v.array(v.number()),
    quality_score: v.number(),
    stored_at: v.string(),
    ttl_expires: v.string(),
  },
  handler: async (ctx, args) => {
    await ctx.db.insert("research_memory", args);
  },
});
