CREATE TABLE "short_links" (
	"id" uuid PRIMARY KEY NOT NULL,
	"original_url" varchar(4096) NOT NULL,
	"short_code" varchar(30) NOT NULL,
	"created_at" timestamp with time zone NOT NULL,
	"expires_at" timestamp with time zone NOT NULL
);
