# Example: User Session Management with Go & Dragonfly

## Introduction

User session management has evolved significantly over time. Traditionally, systems relied on sessions, where each
request within a user session required session identifier validation against a centralized data store. This approach
demanded a high-performance data store to handle the frequent lookups efficiently. With the adoption of the
[JWT (JSON Web Tokens)](https://jwt.io/) standard, session management became stateless,
allowing tokens to be verified purely through computation without requiring a data store. (Read more about the
differences [here](https://stackoverflow.com/questions/43452896/authentication-jwt-usage-vs-session).)
While JWTs offer simplicity and scalability, they have a notable drawback: once issued, they
cannot be revoked server-side and can only be invalidated upon expiration or manually removed on the client side.

To address this limitation, many systems now employ **a combination of access tokens and refresh tokens**.
Access tokens can be short-lived JWTs used for processing most user requests, while refresh tokens are long-lived and
enable session renewal. This hybrid approach ensures both performance (with lightweight stateless access tokens) and
security (by enabling server-side revocation of refresh tokens).

Despite the advantages of this hybrid approach, managing refresh tokens still requires a high-performance data store to
handle operations like token storage, validation, and expiration efficiently. This is where Dragonfly shines as a
modern, multi-threaded, and high-performance in-memory data store. In this example project, Dragonfly is used to manage
user refresh tokens via its [Set](https://www.dragonflydb.io/docs/category/sets) data type, offering several benefits:

- **High Performance:** Dragonfly's multi-threaded architecture ensures rapid access and updates to session data.
- **Multi-Session Management:** Refresh tokens for multiple user sessions (e.g., same user across devices) can be stored
  and managed in a single set.
- **Fine-Grained Expiration:** With
  Dragonfly's [FIELDEXPIRE](https://www.dragonflydb.io/docs/command-reference/generic/fieldexpire)
  and [FIELDTTL](https://www.dragonflydb.io/docs/command-reference/generic/fieldttl) commands, individual refresh tokens
  within a set can have distinct expiration times, offering precise control over token lifecycles.

```shell
# A user can have multiple sessions across different devices.
dragonfly$> SMEMBERS user:0193a31d-73ab-7e29-b0dd-XXXXXXXXXXXX:sessions
1) "08e666c9-9dfe-4f98-bacb-XXXXXXXXXXXX"
2) "fbb55a43-26e8-42b2-9e32-XXXXXXXXXXXX"
3) "0cfcfbe6-9346-4ca2-b7fc-XXXXXXXXXXXX"
4) "ddf31a6b-a776-4042-8a86-XXXXXXXXXXXX"
5) "6cdb1b08-767f-4082-8873-XXXXXXXXXXXX"

# Each session has a distinct refresh token with a unique expiration time.
dragonfly$> FIELDTTL user:0193a31d-73ab-7e29-b0dd-XXXXXXXXXXXX:sessions 08e666c9-9dfe-4f98-bacb-XXXXXXXXXXXX
(integer) 518400 # 6 days
dragonfly$> FIELDTTL user:0193a31d-73ab-7e29-b0dd-XXXXXXXXXXXX:sessions fbb55a43-26e8-42b2-9e32-XXXXXXXXXXXX
(integer) 600    # 10 minutes
```

This project demonstrates how to leverage Dragonfly's set data type to build a scalable, secure, and efficient user
session management system, highlighting why Dragonfly is an excellent choice for this use case.

## Packages Used

- The [go-redis](https://github.com/redis/go-redis) client is used. It has strongly typed methods for various commands.
- The [Fiber](https://github.com/gofiber/fiber) framework is used to build the HTTP server.
  It is a fast, lightweight, and easy-to-use web framework for Go.
- Others:
    - [jwt](https://github.com/golang-jwt/jwt) for generating and verifying JWT tokens.
    - [uuid](https://github.com/google/uuid) for generating and parsing UUIDs.
    - [go-sqlite3](https://github.com/mattn/go-sqlite3) for interacting with the SQLite database. Note that `go-sqlite3`
      is a [CGO-enabled package](https://github.com/mattn/go-sqlite3?tab=readme-ov-file#installation).
    - [crypto](https://pkg.go.dev/golang.org/x/crypto) for hashing and verifying passwords.

## Local Setup

- Note that all the commands should be **executed within the root directory of this example project:**

```shell
# Make sure you are in the correct directory, which is in 'user-session-management-go'.
$> pwd
/path/to/your/dragonfly-examples/user-session-management-go
```

- Make sure that you have [Go v1.23+](https://go.dev/dl/) installed locally.
- Make sure that you have [Docker](https://docs.docker.com/engine/install/) installed locally.
- Make sure that you have [Docker Compose](https://docs.docker.com/compose/install/) installed locally.
- Run a Dragonfly instances locally using Docker Compose:

```bash
# Within the root directory of this example (dragonfly-examples/user-session-management-go):
$> docker compose build --no-cache && docker compose up -d
```

- Install the required Go packages:

```bash
# Within the root directory of this example (dragonfly-examples/user-session-management-go):
$> go mod tidy && go mod vendor
```

- Run the Go application:

```bash
# Within the root directory of this example (dragonfly-examples/user-session-management-go):
$> go run app/main.go
```

- Use the API to register a user:

```bash
$> curl --request POST \
   --url http://localhost:8080/user/register \
   --header 'Content-Type: application/json' \
   --data '{
     "username": "joe",
     "password": "123"
   }'
```

- Use the API to log in a user as below.
  Note that a new login request assumes a new session (i.e., a new device or browser).

```bash
$> curl --request POST \
   --url http://localhost:8080/user/login \
   --header 'Content-Type: application/json' \
   --data '{
     "username": "joe",
     "password": "123"
   }'
```

- Use the API to refresh a user's session with the **refresh token**:

```bash
$> curl --request POST \
   --url http://localhost:8080/user/refresh-token \
   --header 'Authorization: Bearer 0193a31d-XXXXX__8167b120-XXXXX'
```

- Use the API to log out a user with the **refresh token**:

```bash
$> curl --request POST \
   --url http://localhost:8080/user/logout \
   --header 'Authorization: Bearer 0193a31d-XXXXX__8167b120-XXXXX'
```

- Use the API to read restricted data with the **access token**:

```bash
$> curl --request GET \
   --url http://localhost:8080/resource \
   --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.XXXXX.XXXXX'
```
