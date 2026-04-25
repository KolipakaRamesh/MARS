import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // Episodic Memory — Stores complete research sessions
  sessions: defineTable({
    session_id: v.string(),
    query: v.string(),
    subtasks: v.array(v.string()),
    synthesized_answer: v.string(),
    quality_score: v.number(),
    verdict: v.string(),
    iteration_count: v.number(),
    error: v.optional(v.string()),
    timestamp: v.string(),
  }).index("by_session_id", ["session_id"]),

  // Long-term Vector Memory — Stores research snippets for RAG
  research_memory: defineTable({
    content: v.string(),
    embedding: v.array(v.number()),
    quality_score: v.number(),
    stored_at: v.string(),
    ttl_expires: v.string(),
  }).vectorIndex("by_embedding", {
    vectorField: "embedding",
    dimensions: 1536, // Matches text-embedding-3-small
  }),

  // Real-time Agent Execution Tracking
  heartbeats: defineTable({
    session_id: v.string(),
    agent: v.string(),
    status: v.string(),
    subtask_index: v.optional(v.number()),
    subtasks: v.optional(v.array(v.string())),
    last_updated: v.number(),
  }).index("by_session_id", ["session_id"]),
});
