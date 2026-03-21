# PPP (Point-to-Point Protocol)

> **Standard:** [RFC 1661](https://www.rfc-editor.org/rfc/rfc1661) | **Layer:** Data Link (Layer 2) | **Wireshark filter:** `ppp`

PPP is a data link protocol for establishing a direct connection between two nodes. It provides framing, link negotiation (LCP), authentication (PAP/CHAP/EAP), and network-layer configuration (IPCP for IPv4, IPV6CP for IPv6). PPP was the standard protocol for dial-up Internet and remains the foundation of PPPoE (broadband DSL/fiber), PPPoA (ATM), L2TP tunnels, and some serial WAN links.

## Frame

```mermaid
packet-beta
  0-7: "Flag (0x7E)"
  8-15: "Address (0xFF)"
  16-23: "Control (0x03)"
  24-39: "Protocol (16 bits)"
  40-71: "Information (payload) ..."
  72-87: "FCS (16 bits)"
  88-95: "Flag (0x7E)"
```

## Key Fields

| Field | Size | Description |
|-------|------|-------------|
| Flag | 8 bits | HDLC frame delimiter `0x7E` |
| Address | 8 bits | Always `0xFF` (all-stations broadcast) |
| Control | 8 bits | Always `0x03` (unnumbered information) |
| Protocol | 16 bits | Identifies the encapsulated protocol |
| Information | Variable | Payload (default max 1500 bytes, negotiable) |
| FCS | 16 or 32 bits | Frame Check Sequence (CRC-16 default, CRC-32 optional) |

Address and Control fields can be compressed away via LCP negotiation (ACFC), and the Protocol field can be compressed to 1 byte (PFC).

## Protocol Field Values

| Value | Protocol |
|-------|----------|
| 0x0021 | IPv4 |
| 0x0057 | IPv6 |
| 0x002B | IPX |
| 0x8021 | IPCP (IP Control Protocol) |
| 0x8057 | IPV6CP (IPv6 Control Protocol) |
| 0xC021 | LCP (Link Control Protocol) |
| 0xC023 | PAP (Password Authentication Protocol) |
| 0xC223 | CHAP (Challenge Handshake Authentication Protocol) |
| 0xC227 | EAP |
| 0x8281 | MPLSCP |

## Link Establishment

```mermaid
sequenceDiagram
  participant A as Peer A
  participant B as Peer B

  Note over A,B: Physical link up
  A->>B: LCP Configure-Request (MRU, auth, magic number)
  B->>A: LCP Configure-Ack
  B->>A: LCP Configure-Request
  A->>B: LCP Configure-Ack
  Note over A,B: LCP Open — link negotiated

  B->>A: CHAP Challenge
  A->>B: CHAP Response (hash)
  B->>A: CHAP Success
  Note over A,B: Authentication complete

  A->>B: IPCP Configure-Request (IP address)
  B->>A: IPCP Configure-Nak (assigned IP: 10.0.0.2)
  A->>B: IPCP Configure-Request (IP: 10.0.0.2)
  B->>A: IPCP Configure-Ack
  Note over A,B: Network layer up — IP traffic flows
```

## LCP (Link Control Protocol)

| Code | Name | Description |
|------|------|-------------|
| 1 | Configure-Request | Propose link options |
| 2 | Configure-Ack | Accept all options |
| 3 | Configure-Nak | Reject option values (suggest alternatives) |
| 4 | Configure-Reject | Reject option types entirely |
| 5 | Terminate-Request | Close the link |
| 6 | Terminate-Ack | Acknowledge closure |
| 9 | Echo-Request | Keepalive |
| 10 | Echo-Reply | Keepalive response |

### LCP Options

| Type | Name | Description |
|------|------|-------------|
| 1 | MRU | Maximum Receive Unit (default 1500) |
| 3 | Authentication Protocol | PAP (0xC023), CHAP (0xC223), EAP (0xC227) |
| 5 | Magic Number | Loop detection |
| 7 | PFC | Protocol Field Compression |
| 8 | ACFC | Address/Control Field Compression |

## Authentication

| Method | Security | Description |
|--------|----------|-------------|
| PAP | Weak | Sends password in cleartext |
| CHAP | Moderate | Challenge-response with MD5 hash |
| MS-CHAPv2 | Moderate | Microsoft variant with mutual authentication |
| EAP | Strong | Extensible framework (TLS, PEAP, etc.) |

## PPPoE (PPP over Ethernet)

PPPoE encapsulates PPP in Ethernet frames for broadband access (DSL, fiber):

```mermaid
packet-beta
  0-3: "Ver (1)"
  4-7: "Type (1)"
  8-15: "Code"
  16-31: "Session ID"
  32-47: "Length"
  48-63: "PPP Payload ..."
```

### PPPoE Phases

```mermaid
sequenceDiagram
  participant C as Client
  participant S as Access Concentrator

  C->>S: PADI (PPPoE Active Discovery Initiation, broadcast)
  S->>C: PADO (PPPoE Active Discovery Offer)
  C->>S: PADR (PPPoE Active Discovery Request)
  S->>C: PADS (PPPoE Active Discovery Session, session ID assigned)
  Note over C,S: PPP session begins (LCP, Auth, IPCP)

  Note over C,S: Data flows as PPP-in-Ethernet

  C->>S: PADT (PPPoE Active Discovery Terminate)
```

### PPPoE EtherTypes

| EtherType | Phase |
|-----------|-------|
| 0x8863 | Discovery (PADI, PADO, PADR, PADS, PADT) |
| 0x8864 | Session (PPP data) |

### MTU Impact

PPPoE adds 8 bytes of overhead, reducing the effective MTU from 1500 to **1492 bytes** — a common cause of path MTU issues.

## Encapsulation

```mermaid
graph LR
  Serial["Serial link (HDLC)"] --> PPP["PPP"]
  Ethernet["Ethernet (0x8864)"] --> PPPoE["PPPoE"] --> PPP2["PPP"]
  ATM["ATM"] --> PPPoA["PPPoA"] --> PPP3["PPP"]
  L2TP["L2TP tunnel"] --> PPP4["PPP"]
  PPP --> IP["IPv4 / IPv6"]
```

## Standards

| Document | Title |
|----------|-------|
| [RFC 1661](https://www.rfc-editor.org/rfc/rfc1661) | The Point-to-Point Protocol (PPP) |
| [RFC 1662](https://www.rfc-editor.org/rfc/rfc1662) | PPP in HDLC-like Framing |
| [RFC 1332](https://www.rfc-editor.org/rfc/rfc1332) | PPP IPCP (IP Control Protocol) |
| [RFC 5072](https://www.rfc-editor.org/rfc/rfc5072) | PPP IPV6CP (IPv6 Control Protocol) |
| [RFC 1334](https://www.rfc-editor.org/rfc/rfc1334) | PPP Authentication: PAP and CHAP |
| [RFC 2516](https://www.rfc-editor.org/rfc/rfc2516) | PPP over Ethernet (PPPoE) |
| [RFC 2364](https://www.rfc-editor.org/rfc/rfc2364) | PPP over ATM (PPPoA) |

## See Also

- [Ethernet](ethernet.md) — PPPoE carrier
- [IPv4](../network-layer/ip.md) — configured via IPCP
- [RADIUS](../security/radius.md) — authenticates PPP/PPPoE sessions
