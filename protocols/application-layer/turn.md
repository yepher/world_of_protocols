# TURN (Traversal Using Relays around NAT)

> **Standard:** [RFC 8656](https://www.rfc-editor.org/rfc/rfc8656) | **Layer:** Application (Layer 7) | **Wireshark filter:** `stun` (TURN uses STUN message format)

TURN is an extension of STUN that provides a relay server for media traffic when direct peer-to-peer connectivity fails. This happens when both peers are behind symmetric NATs or restrictive firewalls that block incoming UDP. The TURN server allocates a public transport address (the relay address) and forwards packets between the two peers. TURN is the fallback mechanism in ICE — it guarantees connectivity at the cost of routing all media through a server, adding latency and server bandwidth.

## How TURN Works

```mermaid
sequenceDiagram
  participant A as Peer A (behind NAT)
  participant T as TURN Server
  participant B as Peer B

  A->>T: Allocate Request (credentials)
  T->>A: Allocate Response (relayed-address=203.0.113.10:49152)
  Note over A: A now has a public relay address

  A->>T: CreatePermission (peer B's address)
  T->>A: CreatePermission Response

  A->>T: Send Indication (data for B, wrapped)
  T->>B: Forward data (from relay address)
  B->>T: Data to relay address
  T->>A: Data Indication (data from B, wrapped)

  Note over A,B: Or use ChannelBind for more efficient relay:
  A->>T: ChannelBind Request (channel 0x4000 → B's address)
  T->>A: ChannelBind Response
  A->>T: ChannelData (0x4000 + data)
  T->>B: Forward data
```

## Message Format

TURN reuses the [STUN](stun.md) message format (20-byte header with magic cookie) and adds new methods and attributes:

```mermaid
packet-beta
  0-15: "Type (method + class)"
  16-31: "Message Length"
  32-63: "Magic Cookie (0x2112A442)"
  64-95: "Transaction ID ..."
  96-127: "Transaction ID ..."
  128-159: "Transaction ID (96 bits total)"
  160-191: "Attributes ..."
```

## TURN Methods

| Method | Value | Description |
|--------|-------|-------------|
| Allocate | 0x003 | Request a relay allocation |
| Refresh | 0x004 | Keep an allocation alive (or release with lifetime=0) |
| Send | 0x006 | Send data through relay (indication, no response) |
| Data | 0x007 | Receive data through relay (indication from server) |
| CreatePermission | 0x008 | Authorize a peer's IP to send through the relay |
| ChannelBind | 0x009 | Bind a channel number to a peer for efficient relay |

## Key Attributes

| Type | Name | Description |
|------|------|-------------|
| 0x000C | CHANNEL-NUMBER | Channel number for ChannelBind (0x4000-0x7FFF) |
| 0x000D | LIFETIME | Allocation lifetime in seconds (default 600) |
| 0x0012 | XOR-PEER-ADDRESS | Peer's transport address (XOR-encoded) |
| 0x0013 | DATA | Application data being relayed |
| 0x0016 | XOR-RELAYED-ADDRESS | Allocated relay address (XOR-encoded) |
| 0x0019 | REQUESTED-TRANSPORT | Transport protocol for relay (17 = UDP) |
| 0x0022 | RESERVATION-TOKEN | Token for reserving a port pair (RTP/RTCP) |

## ChannelData Message

For efficiency, TURN provides ChannelData messages that bypass the full STUN header. After a ChannelBind, data is sent with a minimal 4-byte header:

```mermaid
packet-beta
  0-15: "Channel Number"
  16-31: "Length"
  32-63: "Application Data ..."
```

| Field | Size | Description |
|-------|------|-------------|
| Channel Number | 16 bits | 0x4000-0x7FFF (distinguishes from STUN by first two bits being `01`) |
| Length | 16 bits | Length of application data |
| Data | Variable | The relayed payload (padded to 4 bytes over UDP) |

ChannelData saves 36+ bytes of overhead per packet compared to Send/Data indications — critical for high-frequency media streams.

## Address Types in TURN/ICE

```mermaid
graph TD
  Host["Host Address<br/>(local IP, e.g., 192.168.1.5:12345)"]
  STUN_Server["STUN Server"]
  TURN_Server["TURN Server"]

  Host -->|STUN Binding| STUN_Server
  STUN_Server -->|XOR-MAPPED-ADDRESS| Srflx["Server Reflexive Address<br/>(NAT's public IP:port)"]

  Host -->|TURN Allocate| TURN_Server
  TURN_Server -->|XOR-RELAYED-ADDRESS| Relay["Relay Address<br/>(TURN server's public IP:port)"]
```

| Candidate Type | Source | Preference (typical) |
|---------------|--------|---------------------|
| Host | Local network interface | Highest |
| Server Reflexive (srflx) | STUN Binding response | Medium |
| Relay | TURN Allocate response | Lowest (but always works) |

## Authentication

TURN requires long-term credentials (unlike STUN Binding which can be unauthenticated):

| Field | Description |
|-------|-------------|
| USERNAME | Client's username |
| REALM | Server's authentication realm |
| NONCE | Server-provided nonce (time-limited) |
| MESSAGE-INTEGRITY | HMAC-SHA1 computed with `MD5(username:realm:password)` |

## Encapsulation

```mermaid
graph LR
  UDP3478["UDP port 3478"] --> TURN_UDP["TURN"]
  TCP3478["TCP port 3478"] --> TURN_TCP["TURN"]
  TLS5349["TLS port 5349"] --> TURN_TLS["TURN over TLS"]
  UDP443["UDP port 443"] --> TURN_443["TURN (firewall traversal)"]
```

## Standards

| Document | Title |
|----------|-------|
| [RFC 8656](https://www.rfc-editor.org/rfc/rfc8656) | Traversal Using Relays around NAT (TURN) |
| [RFC 5766](https://www.rfc-editor.org/rfc/rfc5766) | TURN (previous version) |
| [RFC 6062](https://www.rfc-editor.org/rfc/rfc6062) | TURN Extensions for TCP Allocations |
| [RFC 7065](https://www.rfc-editor.org/rfc/rfc7065) | URI Scheme for TURN |
| [RFC 8489](https://www.rfc-editor.org/rfc/rfc8489) | STUN — base protocol TURN extends |

## See Also

- [STUN](stun.md) — base protocol that TURN extends
- [ICE](ice.md) — orchestrates STUN and TURN for connectivity
- [WebRTC](webrtc.md) — primary consumer of TURN relays
- [UDP](../transport-layer/udp.md)
