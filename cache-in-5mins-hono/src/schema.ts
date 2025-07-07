import { pgTable, uuid, varchar, timestamp } from "drizzle-orm/pg-core";

// Table schema for 'short_links'.
export const shortLinksTable = pgTable("short_links", {
  id: uuid().primaryKey(),
  originalUrl: varchar("original_url", { length: 2048 }).notNull(),
  shortCode: varchar("short_code").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull(),
  expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
});
