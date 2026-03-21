# TFTP (Trivial File Transfer Protocol)

> **Standard:** [RFC 1350](https://www.rfc-editor.org/rfc/rfc1350) | **Layer:** Application (Layer 7) | **Wireshark filter:** `tftp`

TFTP is a minimal file transfer protocol that uses UDP with no authentication, no directory listing, and no encryption. Its simplicity makes it ideal for bootstrapping — PXE network booting, firmware updates on embedded devices, and provisioning IP phones and network equipment. TFTP fits in a very small code footprint, making it implementable on devices with minimal resources. It uses a simple stop-and-wait acknowledgment scheme for reliability over UDP.

## Packet Types

| Opcode | Name | Direction | Description |
|--------|------|-----------|-------------|
| 1 | RRQ | Client → Server | Read Request (download a file) |
| 2 | WRQ | Client → Server | Write Request (upload a file) |
| 3 | DATA | Either | Data block (512 bytes, or less for last block) |
| 4 | ACK | Either | Acknowledge a data block |
| 5 | ERROR | Either | Error message |
| 6 | OACK | Server → Client | Option Acknowledgment (RFC 2347) |

## RRQ / WRQ Format

```mermaid
packet-beta
  0-15: "Opcode (1 or 2)"
  16-31: "Filename (string, null-terminated) ..."
  32-47: "Mode (string, null-terminated) ..."
  48-63: "Options (RFC 2347) ..."
```

## DATA Format

```mermaid
packet-beta
  0-15: "Opcode (3)"
  16-31: "Block Number"
  32-63: "Data (0-512 bytes) ..."
```

## ACK Format

```mermaid
packet-beta
  0-15: "Opcode (4)"
  16-31: "Block Number"
```

## ERROR Format

```mermaid
packet-beta
  0-15: "Opcode (5)"
  16-31: "Error Code"
  32-63: "Error Message (string) ..."
```

## Read Transfer (Download)

```mermaid
sequenceDiagram
  participant C as Client
  participant S as TFTP Server

  C->>S: RRQ (filename="firmware.bin", mode="octet") [port 69]
  Note over S: Server responds from a new ephemeral port
  S->>C: DATA (block=1, 512 bytes) [from port 5000]
  C->>S: ACK (block=1) [to port 5000]
  S->>C: DATA (block=2, 512 bytes)
  C->>S: ACK (block=2)
  S->>C: DATA (block=3, 200 bytes) ← less than 512 = last block
  C->>S: ACK (block=3)
  Note over C,S: Transfer complete
```

The last DATA packet has fewer than 512 bytes (or exactly 0), signaling end of file.

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | Not defined | See error message |
| 1 | File not found | Requested file does not exist |
| 2 | Access violation | Permission denied |
| 3 | Disk full | No space for write |
| 4 | Illegal operation | Unknown opcode or bad request |
| 5 | Unknown transfer ID | Wrong source port (session mismatch) |
| 6 | File already exists | File exists (for write) |
| 7 | No such user | User authentication failed (rarely used) |
| 8 | Option negotiation failed | Requested option rejected |

## Transfer Modes

| Mode | Description |
|------|-------------|
| `netascii` | ASCII text with CR/LF conversion |
| `octet` | Raw binary (most common) |
| `mail` | Email delivery (obsolete) |

## Options (RFC 2347)

| Option | RFC | Description |
|--------|-----|-------------|
| blksize | RFC 2348 | Block size (8-65464 bytes, default 512) |
| tsize | RFC 2349 | Transfer size (total file size in bytes) |
| timeout | RFC 2349 | Retransmission timeout in seconds (1-255) |
| windowsize | RFC 7440 | Number of blocks sent before waiting for ACK |

### Option Negotiation

```mermaid
sequenceDiagram
  participant C as Client
  participant S as Server

  C->>S: RRQ ("firmware.bin", "octet", blksize=1428, tsize=0)
  S->>C: OACK (blksize=1428, tsize=4096000)
  C->>S: ACK (block=0)
  S->>C: DATA (block=1, 1428 bytes)
  C->>S: ACK (block=1)
  Note over C,S: Continue with negotiated block size
```

## Common Uses

| Use Case | Description |
|----------|-------------|
| PXE Boot | BIOS/UEFI downloads bootloader via TFTP after DHCP |
| Cisco IOS | Firmware upload/download on routers/switches |
| VoIP Phones | Configuration file provisioning |
| Firmware Updates | Embedded device firmware loading |
| Network Equipment | Configuration backup/restore |

### PXE Boot Flow

```mermaid
sequenceDiagram
  participant PC as PXE Client
  participant D as DHCP Server
  participant T as TFTP Server

  PC->>D: DHCP Discover
  D->>PC: DHCP Offer (IP + next-server=TFTP + filename=pxelinux.0)
  PC->>T: TFTP RRQ (pxelinux.0)
  T->>PC: TFTP DATA (bootloader)
  Note over PC: Bootloader loads, requests kernel + initrd via TFTP
```

## TFTP vs FTP vs HTTP

| Feature | TFTP | FTP | HTTP |
|---------|------|-----|------|
| Transport | UDP | TCP | TCP |
| Port | 69 | 21 + data | 80/443 |
| Authentication | None | Username/password | Optional |
| Directory listing | No | Yes | No (application-dependent) |
| File size limit | ~32MB (16-bit block#) or larger with options | None | None |
| Encryption | None | FTPS | HTTPS |
| Code footprint | Tiny (~1KB) | Large | Large |
| Use case | Bootstrapping, firmware | General file transfer | Web, APIs |

## Encapsulation

```mermaid
graph LR
  UDP69["UDP port 69 (initial)"] --> TFTP2["TFTP"]
```

The initial request goes to port 69. The server responds from a random ephemeral port, and the rest of the transfer uses that port.

## Standards

| Document | Title |
|----------|-------|
| [RFC 1350](https://www.rfc-editor.org/rfc/rfc1350) | The TFTP Protocol (Revision 2) |
| [RFC 2347](https://www.rfc-editor.org/rfc/rfc2347) | TFTP Option Extension |
| [RFC 2348](https://www.rfc-editor.org/rfc/rfc2348) | TFTP Blocksize Option |
| [RFC 2349](https://www.rfc-editor.org/rfc/rfc2349) | TFTP Timeout and Transfer Size Options |
| [RFC 7440](https://www.rfc-editor.org/rfc/rfc7440) | TFTP Windowsize Option |

## See Also

- [FTP](ftp.md) — full-featured file transfer alternative
- [DHCP](../naming/dhcp.md) — works with TFTP for PXE boot (next-server option)
- [UDP](../transport-layer/udp.md) — TFTP transport
