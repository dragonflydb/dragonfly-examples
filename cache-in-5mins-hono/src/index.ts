import { eq, and, gt } from "drizzle-orm";
import { drizzle } from "drizzle-orm/node-postgres";
import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { Redis as Cache } from "ioredis";
import { stringify as uuidStringify } from "uuid";

import { shortLinksTable } from "./schema";
import * as schema from "./schema";
import {
  shortLinkInsertSchema,
  ShortLinkInsert,
  ShortLinkSelect,
} from "./validator";

// For simplicity, we are using local Redis, Dragonfly, and PostgreSQL instances.
// Please ensure they are running locally and adjust the connection details as needed.
const cache = new Cache({
  host: "localhost",
  // port: 6379, // Redis running locally.
  port: 6380, // Dragonfly running locally.
});

const db = drizzle(
  "postgresql://local_user_dev:local_pwd_dev@localhost:5432/appdb",
  { schema: schema },
);

const app = new Hono();

app.post(
  "/short-links",
  zValidator("json", shortLinkInsertSchema),
  async (c) => {
    // Validate and transform the request.
    const req: ShortLinkInsert = c.req.valid("json");

    // Save the new record in the database.
    await db.insert(shortLinksTable).values(req).execute();

    // Cache the new record in Redis/Dragonfly.
    const expiresAt = Math.trunc(req.expiresAt.getTime() / 1000);
    await cache.set(req.id, req.originalUrl, "EXAT", expiresAt);
    return c.json(req);
  },
);

app.get("/:shortCode", async (c) => {
  // Parse the short code as a UUIDv7.
  const shortCode = c.req.param("shortCode");
  const id = uuidStringify(
    Uint8Array.fromBase64(shortCode, { alphabet: "base64url" }),
  );

  // Read from cache.
  const originalUrl = await cache.get(id);

  // Cache hit: redirect.
  if (originalUrl) {
    return c.redirect(originalUrl);
  }

  // Cache miss: read from database, cache the record again if it exists.
  const result: ShortLinkSelect | undefined =
    await db.query.shortLinksTable.findFirst({
      where: and(
        eq(shortLinksTable.id, id),
        gt(shortLinksTable.expiresAt, new Date()),
      ),
    });
  if (!result) {
    return c.notFound();
  }
  const expiresAt = Math.trunc(result.expiresAt.getTime() / 1000);
  await cache.set(result.id, result.originalUrl, "EXAT", expiresAt);
  return c.redirect(result.originalUrl);
});

export default app;
