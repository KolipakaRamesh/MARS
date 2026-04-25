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
    subtasks: v.optional(v.array(v.string())),
  },
  handler: async (ctx, args) => {
    const existingHeartbeats = await ctx.db
      .query("heartbeats")
      .withIndex("by_session_id", (q) => q.eq("session_id", args.session_id))
      .collect();

    const existing = existingHeartbeats[0];
    // If somehow we have more than one, we'll cleanup the extras later or just patch the first
    if (existingHeartbeats.length > 1) {
      for (let i = 1; i < existingHeartbeats.length; i++) {
        await ctx.db.delete(existingHeartbeats[i]._id);
      }
    }

    const timestamp = Date.now();

    if (existing) {
      await ctx.db.patch(existing._id, {
        agent: args.agent,
        status: args.status,
        subtask_index: args.subtask_index,
        // Only overwrite subtasks if the new heartbeat includes them
        ...(args.subtasks !== undefined ? { subtasks: args.subtasks } : {}),
        last_updated: timestamp,
      });
    } else {
      await ctx.db.insert("heartbeats", {
        session_id: args.session_id,
        agent: args.agent,
        status: args.status,
        subtask_index: args.subtask_index,
        subtasks: args.subtasks,
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
      .first();
  },
});
