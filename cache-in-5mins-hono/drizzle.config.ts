import { defineConfig } from "drizzle-kit";

// For simplicity, we are using a local PostgreSQL instance.
// Please ensure it is running locally and adjust the connection details as needed.
export default defineConfig({
  dialect: "postgresql",
  schema: "./src/schema.ts",
  dbCredentials: {
    url: "postgresql://local_user_dev:local_pwd_dev@localhost:5432/appdb",
  },
});
