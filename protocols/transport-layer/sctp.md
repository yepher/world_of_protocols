# SCTP (Stream Control Transmission Protocol)

> **Standard:** [RFC 9260](https://www.rfc-editor.org/rfc/rfc9260) | **Layer:** Transport (Layer 4) | **Wireshark filter:** `sctp`

SCTP is a reliable, message-oriented transport protocol that combines features of TCP and UDP. It provides reliable delivery like TCP but preserves message boundaries (not a byte stream), supports multiple independent streams within a single association (no head-of-line blocking), and offers multi-homing (multiple IP addresses per endpoint for failover). SCTP is used by SIGTRAN (SS7 over IP), Diameter (LTE AAA), WebRTC data channels (inside DTLS), and some HPC applications.

## Packet

```mermaid
packet-beta
  0-15: "Source Port"
  16-31: "Destination Port"
  32-63: "Verification Tag"
  64-95: "Checksum (CRC-32c)"
  96-127: "Chunk 1 ..."
  128-159: "Chunk 2 ..."
```

An SCTP packet has a 12-byte common header followed by one or more chunks.

## Key Fields

| Field | Size | Description |
|-------|------|-------------|
| Source Port | 16 bits | Sender's port |
| Destination Port | 16 bits | Receiver's port |
| Verification Tag | 32 bits | Association identifier (anti-spoofing) |
| Checksum | 32 bits | CRC-32c over the entire packet |
| Chunks | Variable | One or more typed chunks |

## Chunk Format

```mermaid
packet-beta
  0-7: "Chunk Type"
  8-15: "Chunk Flags"
  16-31: "Chunk Length"
  32-63: "Chunk Value ..."
```

### Chunk Types

| Type | Name | Description |
|------|------|-------------|
| 0 | DATA | User data |
| 1 | INIT | Initiate an association |
| 2 | INIT ACK | Acknowledge initiation (with cookie) |
| 3 | SACK | Selective Acknowledgment |
| 4 | HEARTBEAT | Path keepalive |
| 5 | HEARTBEAT ACK | Heartbeat response |
| 6 | ABORT | Abort the association |
| 7 | SHUTDOWN | Graceful close (no more data from sender) |
| 8 | SHUTDOWN ACK | Acknowledge shutdown |
| 9 | ERROR | Report error conditions |
| 10 | COOKIE ECHO | Send cookie for association validation |
| 11 | COOKIE ACK | Acknowledge cookie |
| 14 | SHUTDOWN COMPLETE | Close complete |
| 0xC0 | FORWARD TSN | Skip undeliverable chunks (RFC 3758) |

## Association Setup (4-Way Handshake)

SCTP uses a 4-way handshake with a cookie to prevent SYN flood attacks:

```mermaid
sequenceDiagram
  participant A as Endpoint A
  participant B as Endpoint B

  A->>B: INIT (my tag, my TSN, addresses, streams)
  B->>A: INIT ACK (my tag, cookie)
  Note over B: B does NOT allocate state yet
  A->>B: COOKIE ECHO (return the cookie)
  Note over B: B validates cookie, allocates state
  B->>A: COOKIE ACK
  Note over A,B: Association established
```

No state is allocated at the responder until the COOKIE ECHO is validated — DoS resistant by design.

## Key Features

### Multi-Streaming

Multiple independent streams within one association — loss on stream 1 doesn't block stream 2:

| Feature | TCP | SCTP |
|---------|-----|------|
| Streams | 1 byte stream | N independent message streams |
| HOL blocking | Yes (one lost segment blocks all) | No (only affected stream stalls) |
| Message boundaries | No (byte stream) | Yes (message-oriented) |

### Multi-Homing

Each endpoint can have multiple IP addresses. If one path fails, traffic fails over:

```mermaid
graph LR
  A["Endpoint A<br/>10.0.1.1 + 10.0.2.1"] --> B["Endpoint B<br/>10.0.3.1 + 10.0.4.1"]
```

HEARTBEAT chunks monitor reachability of each path. On failure, traffic switches to an alternate path.

### Selective Acknowledgment (SACK)

```mermaid
packet-beta
  0-31: "Cumulative TSN Ack"
  32-47: "Advertised Receiver Window"
  48-63: "Number of Gap Blocks"
  64-79: "Number of Duplicate TSNs"
  80-95: "Gap Block 1 Start"
  96-111: "Gap Block 1 End"
  112-127: "..."
```

## SCTP vs TCP vs UDP

| Feature | TCP | UDP | SCTP |
|---------|-----|-----|------|
| Connection | Stream | Connectionless | Association |
| Reliability | Full | None | Full or partial (PR-SCTP) |
| Message boundaries | No | Yes | Yes |
| Multi-streaming | No | N/A | Yes |
| Multi-homing | No | No | Yes |
| Head-of-line blocking | Yes | No | No (per stream) |
| Setup | 3-way handshake | None | 4-way handshake (cookie) |

## Encapsulation

```mermaid
graph LR
  IP132["IP (Protocol 132)"] --> SCTP2["SCTP"]
  SCTP2 --> SIGTRAN2["M3UA / M2UA (SIGTRAN)"]
  SCTP2 --> Diameter["Diameter"]
  DTLS4["DTLS (WebRTC)"] --> SCTP3["SCTP (Data Channels)"]
```

## Standards

| Document | Title |
|----------|-------|
| [RFC 9260](https://www.rfc-editor.org/rfc/rfc9260) | Stream Control Transmission Protocol (current) |
| [RFC 3758](https://www.rfc-editor.org/rfc/rfc3758) | Partial Reliability Extension (PR-SCTP) |
| [RFC 5061](https://www.rfc-editor.org/rfc/rfc5061) | Dynamic Address Reconfiguration |

## See Also

- [TCP](tcp.md) — reliable byte-stream transport
- [UDP](udp.md) — unreliable datagram transport
- [SS7](../telecom/ss7.md) — SIGTRAN carries SS7 over SCTP
- [WebRTC](../application-layer/webrtc.md) — data channels use SCTP over DTLS
