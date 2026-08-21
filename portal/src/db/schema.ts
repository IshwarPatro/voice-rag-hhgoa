import { pgTable, text, serial, doublePrecision, boolean, timestamp } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  name: text('name'),
  email: text('email').unique().notNull(),
  password: text('password'),
  image: text('image'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

export const queries = pgTable('queries', {
  id: serial('id').primaryKey(),
  userId: text('user_id'),
  queryText: text('query_text').notNull(),
  responseText: text('response_text'),
  latencyStt: doublePrecision('latency_stt'),
  latencyModeration: doublePrecision('latency_moderation'),
  latencyRetrieval: doublePrecision('latency_retrieval'),
  latencyLlm: doublePrecision('latency_llm'),
  latencyTotal: doublePrecision('latency_total'),
  isSafe: boolean('is_safe').default(true),
  generatedAt: timestamp('generated_at').defaultNow().notNull(),
});
