# DTLS (Datagram Transport Layer Security)

> **Standard:** [RFC 9147](https://www.rfc-editor.org/rfc/rfc9147) (DTLS 1.3) / [RFC 6347](https://www.rfc-editor.org/rfc/rfc6347) (DTLS 1.2) | **Layer:** Presentation / Security (Layer 6) | **Wireshark filter:** `dtls`

DTLS adapts TLS for unreliable datagram transport (UDP). It provides the same encryption, authentication, and integrity guarantees as TLS but handles packet loss, reordering, and duplication that are inherent to UDP. DTLS is critical for WebRTC (DTLS-SRTP key exchange), VPN protocols (OpenConnect, Cisco AnyConnect), CoAP (IoT), and any application needing encrypted UDP.

## Record

```mermaid
packet-beta
  0-7: "Content Type"
  8-23: "Protocol Version"
  24-39: "Epoch"
  40-87: "Sequence Number (48 bits)"
  88-103: "Length"
  104-135: "Fragment / Payload ..."
```

| Field | Size | Description |
|-------|------|-------------|
| Content Type | 8 bits | Same as TLS (22=Handshake, 23=Application Data, 21=Alert, 25=ACK in 1.3) |
| Protocol Version | 16 bits | 0xFEFD = DTLS 1.2, 0xFEFC = DTLS 1.3 (inverted from TLS) |
| Epoch | 16 bits | Increments on each key change (cipher state) |
| Sequence Number | 48 bits | Per-epoch sequence (anti-replay) |
| Length | 16 bits | Fragment length |
| Fragment | Variable | Encrypted payload |

## Key Differences from TLS

| Feature | TLS | DTLS |
|---------|-----|------|
| Transport | TCP (reliable, ordered) | UDP (unreliable, unordered) |
| Record numbering | Implicit (TCP ordering) | Explicit epoch + sequence number |
| Retransmission | TCP handles it | DTLS handshake has its own retransmit timers |
| Fragmentation | TCP handles it | DTLS fragments handshake messages |
| Replay protection | TCP ordering | Sliding window on sequence numbers |
| Connection ID | Not in TLS 1.3 | Optional (RFC 9146) — survives NAT rebinding |

## Handshake

DTLS adds retransmission, fragmentation, and cookie exchange to the TLS handshake:

### DTLS 1.2 Handshake

```mermaid
sequenceDiagram
  participant C as Client
  participant S as Server

  C->>S: ClientHello
  S->>C: HelloVerifyRequest (cookie)
  C->>S: ClientHello (with cookie)
  S->>C: ServerHello, Certificate, ServerHelloDone
  C->>S: ClientKeyExchange, ChangeCipherSpec, Finished
  S->>C: ChangeCipherSpec, Finished
  Note over C,S: Application data (encrypted)
```

The HelloVerifyRequest/cookie exchange is a DoS mitigation — the server doesn't allocate state until the client proves it can receive at its claimed address.

### DTLS 1.3 Handshake

```mermaid
sequenceDiagram
  participant C as Client
  participant S as Server

  C->>S: ClientHello (+ key_share)
  S->>C: HelloRetryRequest (cookie) [optional]
  C->>S: ClientHello (with cookie, key_share)
  S->>C: ServerHello, {EncryptedExtensions, Certificate, CertificateVerify, Finished}
  C->>S: {Finished}
  Note over C,S: 1-RTT application data
```

### Handshake Message Fragmentation

DTLS handshake messages include additional fields for fragmentation:

```mermaid
packet-beta
  0-7: "Handshake Type"
  8-31: "Length (24 bits)"
  32-47: "Message Sequence"
  48-71: "Fragment Offset (24 bits)"
  72-95: "Fragment Length (24 bits)"
  96-127: "Handshake Body ..."
```

| Field | Description |
|-------|-------------|
| Message Sequence | Orders handshake messages (survives reordering) |
| Fragment Offset | Byte offset of this fragment within the full message |
| Fragment Length | Length of this fragment |

## DTLS-SRTP (WebRTC)

In WebRTC, DTLS provides key exchange for SRTP media encryption:

```mermaid
graph LR
  DTLS["DTLS Handshake<br/>(key exchange)"] --> Keys["SRTP Master Key<br/>+ Salt"]
  Keys --> SRTP2["SRTP<br/>(encrypted media)"]
  Keys --> SRTCP2["SRTCP<br/>(encrypted control)"]
```

The DTLS fingerprint is exchanged in SDP (`a=fingerprint:sha-256 ...`) and verified during the handshake — this provides end-to-end authentication without a certificate authority.

## Encapsulation

```mermaid
graph LR
  UDP["UDP"] --> DTLS2["DTLS"]
  DTLS2 --> AppData["Application Data"]
  DTLS2 --> SCTP_DC["SCTP (WebRTC Data Channel)"]
  DTLS2 --> CoAP["CoAP (IoT)"]
```

## Standards

| Document | Title |
|----------|-------|
| [RFC 9147](https://www.rfc-editor.org/rfc/rfc9147) | DTLS 1.3 |
| [RFC 6347](https://www.rfc-editor.org/rfc/rfc6347) | DTLS 1.2 |
| [RFC 5764](https://www.rfc-editor.org/rfc/rfc5764) | DTLS-SRTP (WebRTC key exchange) |
| [RFC 9146](https://www.rfc-editor.org/rfc/rfc9146) | DTLS Connection ID |

## See Also

- [TLS](tls.md) — TCP equivalent
- [WebRTC](webrtc.md) — primary consumer of DTLS-SRTP
- [SRTP](srtp.md) — media encryption keyed by DTLS
- [UDP](../transport-layer/udp.md)
