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
 * Remove all records associated with a session_id (robust cleanup).
 */
export const remove = mutation({
  args: { session_id: v.string() },
  handler: async (ctx, args) => {
    console.log("Convex: remove triggered for session_id", args.session_id);
    
    // Find and delete all session records for this ID
    const sessions = await ctx.db
      .query("sessions")
      .withIndex("by_session_id", (q) => q.eq("session_id", args.session_id))
      .collect();

    console.log(`Convex: Found ${sessions.length} sessions to delete`);
    for (const s of sessions) {
      await ctx.db.delete(s._id);
    }

    // Cleanup heartbeats
    const heartbeats = await ctx.db
      .query("heartbeats")
      .withIndex("by_session_id", (q) => q.eq("session_id", args.session_id))
      .collect();

    console.log(`Convex: Found ${heartbeats.length} heartbeats to delete`);
    for (const hb of heartbeats) {
      await ctx.db.delete(hb._id);
    }
    
    return { success: true, deletedSessions: sessions.length };
  },
});
