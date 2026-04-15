import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

/**
 * Update the live status of an agent within a session.
 */
export const update = mutation({
  args: {
    session_id: v.string(),
    agent: v.string(),
    status: v.string(),
    subtask_index: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("heartbeats")
      .withIndex("by_session_id", (q) => q.eq("session_id", args.session_id))
      .unique();

    const timestamp = Date.now();

    if (existing) {
      await ctx.db.patch(existing._id, {
        agent: args.agent,
        status: args.status,
        subtask_index: args.subtask_index,
        last_updated: timestamp,
      });
    } else {
      await ctx.db.insert("heartbeats", {
        session_id: args.session_id,
        agent: args.agent,
        status: args.status,
        subtask_index: args.subtask_index,
        last_updated: timestamp,
      });
    }
  },
});

/**
 * Get the live status for a session.
 */
export const getStatus = query({
  args: { session_id: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("heartbeats")
      .withIndex("by_session_id", (q) => q.eq("session_id", args.session_id))
      .unique();
  },
});
