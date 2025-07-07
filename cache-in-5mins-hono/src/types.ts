import { z } from "zod/v4";
import {
  pgTable,
  uuid,
  varchar,
  timestamp,
  integer,
} from "drizzle-orm/pg-core";
import { createInsertSchema, createSelectSchema } from "drizzle-zod";
import { v7 as uuidv7, parse as uuidParse } from "uuid";

// Table schema for 'short_links'.
export const shortLinks = pgTable("short_links", {
  id: uuid().primaryKey(),
  originalUrl: varchar("original_url", { length: 2048 }).notNull(),
  shortCode: varchar("short_code").notNull(),
  clicks: integer("clicks").notNull().default(0),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull(),
  expiresAt: timestamp("expires_at", { withTimezone: true }),
});

// Validator and transformer for creating a new 'short_links' entry.
export const shortLinkInsertSchema = createInsertSchema(shortLinks, {
  originalUrl: (val) => z.url(),
  expiresAt: z.coerce.date().optional(),
})
  .omit({
    id: true,
    shortCode: true,
    clicks: true,
    createdAt: true,
  })
  .transform((data) => {
    const id = uuidv7();
    const now = new Date();
    return {
      ...data,
      id,
      shortCode: uuidParse(id).toBase64({ alphabet: "base64url", omitPadding: true }),
      clicks: 0,
      createdAt: now,
    };
  });
export type ShortLinkInsert = z.infer<typeof shortLinkInsertSchema>;

// Validator for selecting 'short_links' entries.
const shortLinkSelectSchema = createSelectSchema(shortLinks);
export type ShortLinkSelect = z.infer<typeof shortLinkSelectSchema>;

const val = {
  originalUrl: "https://www.google.com/",
  expiresAt: "2025-07-07T03:19:01.972Z",
};

console.log(shortLinkInsertSchema.parse(val));
