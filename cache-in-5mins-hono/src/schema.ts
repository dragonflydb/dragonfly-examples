import { pgTable, uuid, varchar, timestamp } from "drizzle-orm/pg-core";

// Table schema for 'short_links'.
export const shortLinksTable = pgTable("short_links", {
  id: uuid().primaryKey(),
  // The length varies for different browsers and systems. 4096 is a safe value that covers most use cases and is the default value for NGINX.
  originalUrl: varchar("original_url", { length: 4096 }).notNull(),
  // In our implementation, the short code is the base64-encoded ID (which is a UUID) without padding, taking 22 characters.
  shortCode: varchar("short_code", { length: 30 }).notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull(),
  expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
});
