# PostgreSQL Wire Protocol

> **Standard:** [PostgreSQL Frontend/Backend Protocol](https://www.postgresql.org/docs/current/protocol.html) | **Layer:** Application (Layer 7) | **Wireshark filter:** `pgsql`

The PostgreSQL wire protocol is a message-based, binary protocol for communication between clients (frontends) and the PostgreSQL database server (backend). Messages are typed and length-prefixed. The protocol supports two query sub-protocols: the Simple Query protocol (send SQL text, get results) and the Extended Query protocol (parse, bind, execute as separate steps, enabling prepared statements and portals). PostgreSQL also defines a COPY sub-protocol for bulk data transfer and an asynchronous notification mechanism (LISTEN/NOTIFY). It runs on TCP port 5432 by default.

## Message Format

### Frontend (Client) and Backend (Server) Messages

All messages after the startup phase share this format:

```mermaid
packet-beta
  0-7: "Type (1 byte)"
  8-39: "Length (4 bytes, includes self)"
  40-71: "Payload ..."
```

### Startup Message (no type byte)

The initial startup message omits the type byte:

```mermaid
packet-beta
  0-31: "Length (4 bytes, includes self)"
  32-47: "Protocol Major (3)"
  48-63: "Protocol Minor (0)"
  64-127: "Parameter name/value pairs (NUL-terminated) ..."
```

## Key Fields

| Field | Size | Description |
|-------|------|-------------|
| Type | 1 byte | Single ASCII character identifying the message type (omitted in startup) |
| Length | 4 bytes | Total length of message including the length field itself but not the type byte |
| Payload | Variable | Message-specific data |

## Connection Phase

### Startup and Authentication

```mermaid
sequenceDiagram
  participant C as Client (Frontend)
  participant S as PostgreSQL (Backend)

  C->>S: StartupMessage (version=3.0, user=alice, database=mydb)
  alt Password Auth
    S->>C: AuthenticationMD5Password (salt)
    C->>S: PasswordMessage (md5 hash)
  else SASL Auth (SCRAM-SHA-256)
    S->>C: AuthenticationSASL (mechanisms: SCRAM-SHA-256)
    C->>S: SASLInitialResponse (client-first-message)
    S->>C: AuthenticationSASLContinue (server-first-message)
    C->>S: SASLResponse (client-final-message)
    S->>C: AuthenticationSASLFinal (server-final-message)
  end
  S->>C: AuthenticationOk
  S->>C: ParameterStatus (server_version = 16.2)
  S->>C: ParameterStatus (server_encoding = UTF8)
  S->>C: ParameterStatus (...)
  S->>C: BackendKeyData (PID, secret key)
  S->>C: ReadyForQuery (transaction status: I=idle)
```

### SSL Negotiation

```mermaid
sequenceDiagram
  participant C as Client (Frontend)
  participant S as PostgreSQL (Backend)

  C->>S: SSLRequest (int32 length, int32 code=80877103)
  alt SSL Supported
    S->>C: 'S' (single byte)
    Note over C,S: TLS handshake begins
  else SSL Not Supported
    S->>C: 'N' (single byte)
    Note over C,S: Continue unencrypted or disconnect
  end
  C->>S: StartupMessage (over TLS if negotiated)
```

## Authentication Types

| Code | Type | Description |
|------|------|-------------|
| 0 | AuthenticationOk | Authentication successful |
| 2 | AuthenticationKerberosV5 | Kerberos V5 required (deprecated) |
| 3 | AuthenticationCleartextPassword | Cleartext password required |
| 5 | AuthenticationMD5Password | MD5 password hash required (with 4-byte salt) |
| 7 | AuthenticationGSS | GSSAPI authentication |
| 9 | AuthenticationSSPI | SSPI authentication (Windows) |
| 10 | AuthenticationSASL | SASL mechanism negotiation (SCRAM-SHA-256) |
| 11 | AuthenticationSASLContinue | SASL challenge |
| 12 | AuthenticationSASLFinal | SASL completion |

## Frontend Messages (Client to Server)

| Type | Name | Description |
|------|------|-------------|
| Q | Query | Execute a simple SQL query (text) |
| P | Parse | Parse a SQL statement into a prepared statement |
| B | Bind | Bind parameters to a prepared statement, creating a portal |
| D | Describe | Describe a prepared statement (S) or portal (P) |
| E | Execute | Execute a portal |
| H | Flush | Force server to deliver pending output |
| S | Sync | Synchronization point (ends extended query, triggers ReadyForQuery) |
| C | Close | Close a prepared statement or portal |
| X | Terminate | Disconnect cleanly |
| d | CopyData | Data chunk during COPY operation |
| c | CopyDone | COPY operation complete |
| f | CopyFail | COPY operation failed |
| p | PasswordMessage / SASLResponse | Authentication data |
| F | FunctionCall | Call a server function by OID (legacy) |

## Backend Messages (Server to Client)

| Type | Name | Description |
|------|------|-------------|
| R | Authentication* | Authentication request or result |
| K | BackendKeyData | Process ID and secret key for cancel requests |
| S | ParameterStatus | Runtime parameter value (e.g., server_encoding) |
| Z | ReadyForQuery | Server is ready; includes transaction status (I/T/E) |
| T | RowDescription | Column metadata for upcoming rows |
| D | DataRow | One row of result data |
| C | CommandComplete | SQL command completed (with row count) |
| I | EmptyQueryResponse | Response to an empty query string |
| E | ErrorResponse | Error with severity, code, message, detail, hint |
| N | NoticeResponse | Non-fatal warning or notice |
| 1 | ParseComplete | Parse step succeeded |
| 2 | BindComplete | Bind step succeeded |
| 3 | CloseComplete | Close step succeeded |
| n | NoData | Describe returned no row info (e.g., for INSERT) |
| t | ParameterDescription | Parameter types for a prepared statement |
| G | CopyInResponse | Server is ready to receive COPY data |
| H | CopyOutResponse | Server is sending COPY data |
| d | CopyData | Data chunk during COPY OUT |
| c | CopyDone | COPY OUT complete |
| A | NotificationResponse | Asynchronous NOTIFY payload |

## Simple Query Protocol

```mermaid
sequenceDiagram
  participant C as Client (Frontend)
  participant S as PostgreSQL (Backend)

  C->>S: Query ("SELECT id, name FROM users")
  S->>C: RowDescription (2 fields: id INT4, name TEXT)
  S->>C: DataRow ("1", "Alice")
  S->>C: DataRow ("2", "Bob")
  S->>C: CommandComplete ("SELECT 2")
  S->>C: ReadyForQuery (I = idle)
```

## Extended Query Protocol

The extended protocol separates parsing, binding, and execution for prepared statements and parameterized queries:

```mermaid
sequenceDiagram
  participant C as Client (Frontend)
  participant S as PostgreSQL (Backend)

  C->>S: Parse (stmt="s1", query="SELECT * FROM users WHERE id = $1", paramTypes=[INT4])
  C->>S: Bind (portal="", stmt="s1", params=[42], resultFormats=[text])
  C->>S: Describe (portal="")
  C->>S: Execute (portal="", maxRows=0)
  C->>S: Sync

  S->>C: ParseComplete
  S->>C: BindComplete
  S->>C: RowDescription (3 fields: id, name, email)
  S->>C: DataRow (42, "Alice", "alice@example.com")
  S->>C: CommandComplete ("SELECT 1")
  S->>C: ReadyForQuery (I)
```

## COPY Protocol

Bulk data transfer for imports and exports:

```mermaid
sequenceDiagram
  participant C as Client (Frontend)
  participant S as PostgreSQL (Backend)

  Note over C,S: COPY IN (client to server)
  C->>S: Query ("COPY users FROM STDIN WITH (FORMAT csv)")
  S->>C: CopyInResponse (format=text, columns=3)
  C->>S: CopyData ("1,Alice,alice@example.com\n")
  C->>S: CopyData ("2,Bob,bob@example.com\n")
  C->>S: CopyDone
  S->>C: CommandComplete ("COPY 2")
  S->>C: ReadyForQuery (I)
```

## LISTEN/NOTIFY (Async Notifications)

```mermaid
sequenceDiagram
  participant C1 as Listener
  participant S as PostgreSQL
  participant C2 as Notifier

  C1->>S: Query ("LISTEN new_orders")
  S->>C1: CommandComplete
  S->>C1: ReadyForQuery (I)

  C2->>S: Query ("NOTIFY new_orders, 'order_id=42'")
  S->>C2: CommandComplete
  S->>C2: ReadyForQuery (I)

  S->>C1: NotificationResponse (PID, channel=new_orders, payload=order_id=42)
```

## ReadyForQuery Transaction Status

| Status | Meaning |
|--------|---------|
| I | Idle (not in a transaction) |
| T | In a transaction block |
| E | In a failed transaction block (queries will be rejected until ROLLBACK) |

## ErrorResponse Fields

| Code | Field | Description |
|------|-------|-------------|
| S | Severity | ERROR, FATAL, PANIC, WARNING, NOTICE, DEBUG, INFO, LOG |
| V | Severity (non-localized) | Always English severity |
| C | Code | SQLSTATE error code (5 characters, e.g., 42P01) |
| M | Message | Primary human-readable error message |
| D | Detail | Optional detailed error explanation |
| H | Hint | Optional suggestion for fixing the problem |
| P | Position | Cursor position in the query string |
| W | Where | Call stack context (PL/pgSQL) |

## Encapsulation

```mermaid
graph LR
  TCP5432["TCP port 5432"] --> PgSQL["PostgreSQL Protocol"]
  TCP5432_TLS["TCP port 5432"] --> TLS["TLS (after SSLRequest)"] --> PgSQL_TLS["PostgreSQL Protocol"]
```

## Standards

| Document | Title |
|----------|-------|
| [Frontend/Backend Protocol](https://www.postgresql.org/docs/current/protocol.html) | PostgreSQL Wire Protocol specification |
| [Message Flow](https://www.postgresql.org/docs/current/protocol-flow.html) | Protocol message flow documentation |
| [Message Formats](https://www.postgresql.org/docs/current/protocol-message-formats.html) | Detailed message format reference |
| [Error Codes](https://www.postgresql.org/docs/current/errcodes-appendix.html) | PostgreSQL SQLSTATE error codes |
| [SCRAM Authentication](https://www.postgresql.org/docs/current/sasl-authentication.html) | SASL/SCRAM-SHA-256 authentication |

## See Also

- [MySQL](mysql.md) -- client/server database wire protocol
- [TDS](tds.md) -- Microsoft SQL Server and Sybase wire protocol
- [Redis](redis.md) -- in-memory data store protocol
- [TCP](../transport-layer/tcp.md)
- [TLS](../security/tls.md) -- encrypts PostgreSQL connections
