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
/**
 * Remove a session and its associated heartbeat by Convex ID.
 */
export const remove = mutation({
  args: { id: v.id("sessions") },
  handler: async (ctx, args) => {
    const session = await ctx.db.get(args.id);
    if (!session) return;

    const sessionId = session.session_id;
    await ctx.db.delete(args.id);

    // Also cleanup the heartbeat(s)
    const heartbeats = await ctx.db
      .query("heartbeats")
      .withIndex("by_session_id", (q) => q.eq("session_id", sessionId))
      .collect();

    for (const hb of heartbeats) {
      await ctx.db.delete(hb._id);
    }
  },
});
