import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

/**
 * Log a completed research session to the database.
 */
export const logSession = mutation({
  args: {
    session_id: v.string(),
    query: v.string(),
    subtasks: v.array(v.string()),
    synthesized_answer: v.string(),
    quality_score: v.number(),
    verdict: v.string(),
    iteration_count: v.number(),
    error: v.optional(v.string()),
    timestamp: v.string(),
  },
  handler: async (ctx, args) => {
    const id = await ctx.db.insert("sessions", args);
    return id;
  },
});

/**
 * Retrieve recent sessions for the UI sidebar.
 */
export const getRecentSessions = query({
  args: { limit: v.number() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("sessions")
      .order("desc")
      .take(args.limit);
  },
});
