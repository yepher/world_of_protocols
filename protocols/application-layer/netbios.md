# NetBIOS (Network Basic Input/Output System)

> **Standard:** [RFC 1001](https://www.rfc-editor.org/rfc/rfc1001) / [RFC 1002](https://www.rfc-editor.org/rfc/rfc1002) | **Layer:** Session (Layer 5) | **Wireshark filter:** `nbns` or `nbss` or `nbds`

NetBIOS is a session-layer API and protocol suite originally developed by IBM in 1983 for LAN communication. It provides name registration/resolution, session establishment, and datagram services for applications on a local network. While the original NetBIOS ran over NetBEUI (a non-routable protocol), the dominant implementation today is **NetBIOS over TCP/IP (NBT)**, which encapsulates NetBIOS services in TCP and UDP. NetBIOS is the foundation of Windows file and printer sharing — SMB historically depended on NetBIOS for name resolution and session transport, though modern SMB can run directly over TCP without it.

## Three Services

| Service | Transport | Port | Description |
|---------|-----------|------|-------------|
| Name Service (NBNS) | UDP | 137 | Name registration, resolution, and release |
| Datagram Service (NBDS) | UDP | 138 | Connectionless messaging |
| Session Service (NBSS) | TCP | 139 | Connection-oriented data transfer |

## Name Service (NBNS — Port 137)

NetBIOS names are 16 bytes: 15 characters of name + 1 byte suffix indicating the service type.

### Name Header

```mermaid
packet-beta
  0-15: "Transaction ID"
  16: "R"
  17-20: "Opcode"
  21-24: "Flags (AA, TC, RD, RA)"
  25-27: "Rcode"
  28-31: "Reserved"
  32-47: "QDCOUNT"
  48-63: "ANCOUNT"
  64-79: "NSCOUNT"
  80-95: "ARCOUNT"
```

The format is based on DNS (RFC 1002 specifies NetBIOS name encoding within DNS-format messages).

### Name Operations

| Opcode | Operation | Description |
|--------|-----------|-------------|
| 0 | Query | Resolve a NetBIOS name to an IP address |
| 5 | Registration | Register a name on the network |
| 6 | Release | Release a registered name |
| 7 | WACK | Wait for Acknowledgment (name registration pending) |
| 8 | Refresh | Refresh a name registration |

### Name Suffixes (16th byte)

| Suffix | Type | Description |
|--------|------|-------------|
| 0x00 | Unique | Workstation service |
| 0x03 | Unique | Messenger service (Windows messaging) |
| 0x20 | Unique | File server service (SMB) |
| 0x1B | Unique | Domain Master Browser |
| 0x1C | Group | Domain Controllers |
| 0x1D | Unique | Master Browser |
| 0x1E | Group | Browser Service Elections |

### Name Resolution Methods

| Method | Description |
|--------|-------------|
| B-node (Broadcast) | Broadcast query on local subnet |
| P-node (Point-to-point) | Query WINS server directly |
| M-node (Mixed) | Broadcast first, then WINS |
| H-node (Hybrid) | WINS first, then broadcast (Windows default) |

## Session Service (NBSS — Port 139)

Provides reliable, connection-oriented transport for SMB and other NetBIOS applications:

### Session Packet

```mermaid
packet-beta
  0-7: "Type"
  8: "Flags"
  9-23: "Length (17 bits)"
  24-55: "Payload ..."
```

### Session Message Types

| Type | Name | Description |
|------|------|-------------|
| 0x00 | Session Message | User data (typically SMB) |
| 0x81 | Session Request | Initiate a session (called/calling names) |
| 0x82 | Positive Response | Session request accepted |
| 0x83 | Negative Response | Session request rejected |
| 0x84 | Retarget Response | Redirect to different IP/port |
| 0x85 | Keep Alive | Session keepalive |

### Session Establishment

```mermaid
sequenceDiagram
  participant C as Client
  participant S as Server

  Note over C: Resolve server name via NBNS (port 137)
  C->>S: Session Request (port 139, called=SERVER<20>, calling=CLIENT<00>)
  S->>C: Positive Session Response
  Note over C,S: NetBIOS session established
  C->>S: Session Message (SMB Negotiate)
  Note over C,S: SMB protocol begins inside the session
```

## Datagram Service (NBDS — Port 138)

Connectionless messaging for broadcasts and group communications:

### Datagram Header

```mermaid
packet-beta
  0-7: "Msg Type"
  8-15: "Flags"
  16-31: "Datagram ID"
  32-63: "Source IP"
  64-79: "Source Port"
  80-95: "Datagram Length"
  96-111: "Packet Offset"
  112-127: "Source Name ..."
  128-143: "Dest Name ..."
  144-175: "User Data ..."
```

| Type | Name | Description |
|------|------|-------------|
| 0x10 | Direct Unique | Datagram to a specific name |
| 0x11 | Direct Group | Datagram to a group name |
| 0x12 | Broadcast | Datagram to all nodes |

## NetBIOS vs Direct SMB

| Feature | NetBIOS over TCP (NBT) | Direct SMB |
|---------|------------------------|------------|
| Port | TCP 139 / UDP 137-138 | TCP 445 |
| Name resolution | NBNS (broadcast or WINS) | DNS |
| Required for SMB | Windows 9x/NT era | Windows 2000+ can use direct |
| Overhead | NetBIOS session framing | None (SMB directly over TCP) |
| Modern status | Legacy, often disabled | Preferred |

## Encapsulation

```mermaid
graph LR
  UDP137["UDP port 137"] --> NBNS["NBNS (Name Service)"]
  UDP138["UDP port 138"] --> NBDS["NBDS (Datagram Service)"]
  TCP139["TCP port 139"] --> NBSS["NBSS (Session Service)"]
  NBSS --> SMB["SMB / CIFS"]
```

## Standards

| Document | Title |
|----------|-------|
| [RFC 1001](https://www.rfc-editor.org/rfc/rfc1001) | Protocol Standard for a NetBIOS Service on a TCP/UDP Transport: Concepts and Methods |
| [RFC 1002](https://www.rfc-editor.org/rfc/rfc1002) | Protocol Standard for a NetBIOS Service on a TCP/UDP Transport: Detailed Specifications |

## See Also

- [SMB](smb.md) — file sharing protocol that historically runs over NetBIOS
- [DNS](dns.md) — modern replacement for NetBIOS name resolution
- [TCP](../transport-layer/tcp.md)
- [UDP](../transport-layer/udp.md)
