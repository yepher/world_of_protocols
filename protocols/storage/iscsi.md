# iSCSI (Internet Small Computer Systems Interface)

> **Standard:** [RFC 7143](https://www.rfc-editor.org/rfc/rfc7143) | **Layer:** Application (SCSI over TCP/IP) | **Wireshark filter:** `iscsi`

iSCSI maps the SCSI command set onto TCP/IP, allowing block-level storage access over standard Ethernet networks. An initiator (client) sends SCSI commands encapsulated in iSCSI PDUs to a target (storage device or array) over one or more TCP connections on port 3260. iSCSI brought SAN-class storage to commodity networks, eliminating the need for dedicated Fibre Channel fabrics. It remains widely deployed in enterprise environments alongside newer protocols like NVMe-oF.

## Basic Header Segment (BHS) — 48 bytes

Every iSCSI PDU begins with a 48-byte Basic Header Segment:

```mermaid
packet-beta
  0-5: "Opcode (6)"
  6: "I"
  7: "F"
  8-15: "Opcode-specific"
  16-23: "Total AHS Length"
  24-31: "Data Segment Length (high)"
  32-63: "Data Segment Length (low 32)"
  64-95: "LUN (high 32)"
  96-127: "LUN (low 32)"
  128-159: "Initiator Task Tag (ITT)"
  160-191: "Opcode-specific / Target Transfer Tag"
  192-223: "CmdSN"
  224-255: "ExpStatSN"
  256-383: "Opcode-specific (128 bits)"
```

## Key Fields

| Field | Size | Description |
|-------|------|-------------|
| Opcode | 6 bits | PDU type (command, response, data, login, etc.) |
| I (Immediate) | 1 bit | Immediate delivery — not queued in command window |
| F (Final) | 1 bit | Final PDU in a sequence |
| TotalAHSLength | 8 bits | Length of Additional Header Segments in 4-byte words |
| DataSegmentLength | 24 bits | Length of data segment in bytes |
| LUN | 64 bits | Logical Unit Number — identifies storage volume |
| ITT (Initiator Task Tag) | 32 bits | Unique tag matching commands to responses |
| CmdSN | 32 bits | Command Sequence Number — ordered command delivery |
| ExpStatSN | 32 bits | Expected Status Sequence Number — flow control |

## PDU Types (Opcodes)

### Initiator Opcodes

| Opcode | Name | Description |
|--------|------|-------------|
| 0x00 | NOP-Out | Keepalive / ping from initiator |
| 0x01 | SCSI Command | Carries a SCSI CDB to the target |
| 0x02 | Task Management Request | Abort task, LUN reset, target reset |
| 0x03 | Login Request | Session establishment and negotiation |
| 0x04 | Text Request | Parameter negotiation after login |
| 0x05 | Data-Out | Write data from initiator to target |
| 0x06 | Logout Request | Session teardown |
| 0x10 | SNACK | Request retransmission of a PDU |

### Target Opcodes

| Opcode | Name | Description |
|--------|------|-------------|
| 0x20 | NOP-In | Keepalive / ping response from target |
| 0x21 | SCSI Response | Status and sense data for a SCSI command |
| 0x22 | Task Management Response | Result of a task management request |
| 0x23 | Login Response | Login phase reply with negotiation parameters |
| 0x24 | Text Response | Parameter negotiation reply |
| 0x25 | Data-In | Read data from target to initiator |
| 0x26 | Logout Response | Logout acknowledgment |
| 0x31 | Ready to Transfer (R2T) | Target solicits write data from initiator |
| 0x32 | Async Message | Asynchronous event notification |
| 0x3F | Reject | Target rejects a PDU |

## Login Phase

The login phase establishes a session and negotiates parameters before any SCSI commands can be exchanged:

```mermaid
sequenceDiagram
  participant I as Initiator
  participant T as Target (port 3260)

  I->>T: TCP SYN
  T->>I: TCP SYN-ACK
  I->>T: TCP ACK

  Note over I,T: Security Negotiation Phase
  I->>T: Login Request (CSG=SecurityNegotiation, NSG=OperationalNegotiation)
  T->>I: Login Response (CHAP challenge)
  I->>T: Login Request (CHAP response + challenge)
  T->>I: Login Response (CHAP mutual response, Transit=1)

  Note over I,T: Operational Parameter Negotiation Phase
  I->>T: Login Request (key=value pairs: MaxRecvDataSegmentLength, etc.)
  T->>I: Login Response (accepted/negotiated values, Status=Success)

  Note over I,T: Full Feature Phase — SCSI commands allowed
  I->>T: SCSI Command (READ)
  T->>I: Data-In + SCSI Response (status)
```

### Login Phases

| Phase | CSG Value | Description |
|-------|-----------|-------------|
| Security Negotiation | 0 | Authentication (CHAP, SRP, Kerberos) |
| Operational Negotiation | 1 | Negotiate parameters (burst lengths, queuing) |
| Full Feature Phase | 3 | SCSI command processing |

## SCSI Read Flow

```mermaid
sequenceDiagram
  participant I as Initiator
  participant T as Target

  I->>T: SCSI Command (READ, LUN, LBA, length)
  T->>I: Data-In (read data, F=0)
  T->>I: Data-In (read data, F=0)
  T->>I: Data-In (read data, F=1) + SCSI Response (Status=Good)
```

## SCSI Write Flow

```mermaid
sequenceDiagram
  participant I as Initiator
  participant T as Target

  I->>T: SCSI Command (WRITE, LUN, LBA, length)
  T->>I: R2T (Ready to Transfer, offset, length)
  I->>T: Data-Out (write data, F=0)
  I->>T: Data-Out (write data, F=1)
  T->>I: SCSI Response (Status=Good)
```

## Key Negotiation Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| MaxRecvDataSegmentLength | 8192 | Maximum data segment size per PDU |
| MaxBurstLength | 262144 | Maximum unsolicited + solicited data per command |
| FirstBurstLength | 65536 | Maximum unsolicited data with immediate write |
| MaxConnections | 1 | Number of TCP connections per session |
| MaxOutstandingR2T | 1 | Outstanding R2T PDUs before more data |
| InitialR2T | Yes | Require R2T before sending write data |
| ImmediateData | Yes | Allow data with the command PDU |
| ErrorRecoveryLevel | 0 | 0=session, 1=digest, 2=connection recovery |
| HeaderDigest | None | CRC32C integrity check on headers |
| DataDigest | None | CRC32C integrity check on data |

## Naming and Discovery

### iSCSI Qualified Name (IQN)

Format: `iqn.YYYY-MM.reversed.domain:identifier`

Example: `iqn.2024-01.com.example:storage.lun0`

### Discovery Methods

| Method | Description |
|--------|-------------|
| Static | Manually configured target addresses |
| SendTargets | Query a known target portal for available targets |
| iSNS | Internet Storage Name Service — centralized discovery and management |
| SLP | Service Location Protocol (less common) |

### SendTargets Discovery

```mermaid
sequenceDiagram
  participant I as Initiator
  participant T as Target Portal

  I->>T: Login (Discovery session)
  T->>I: Login Response (Success)
  I->>T: Text Request (SendTargets=All)
  T->>I: Text Response (TargetName=iqn.xxx, TargetAddress=10.0.0.5:3260)
  I->>T: Logout
```

## Session Architecture

| Concept | Description |
|---------|-------------|
| Session | Initiator-to-target relationship (one or more connections) |
| Connection | Single TCP connection within a session |
| ISID | Initiator Session ID — identifies the session |
| TSIH | Target Session Identifying Handle — assigned by target |
| CID | Connection ID within a session |
| CmdSN Window | Flow control — target advertises ExpCmdSN to MaxCmdSN |

## Protocol Comparison

| Feature | iSCSI | Fibre Channel | NVMe-oF (TCP) |
|---------|-------|---------------|---------------|
| Transport | TCP/IP (Ethernet) | Dedicated FC fabric | TCP/IP (Ethernet) |
| Default Port | 3260 | N/A (lossless fabric) | 4420 |
| Latency | 100-500 us | 10-50 us | 50-200 us |
| Protocol Overhead | SCSI + iSCSI + TCP | SCSI + FCP | NVMe (native) |
| Queue Depth | Negotiated (128-256 typical) | Per-exchange | 64K queues x 64K depth |
| Network | Standard Ethernet | FC switches (dedicated) | Standard Ethernet |
| Cost | Low (commodity HW) | High (dedicated fabric) | Low-Medium |

## Encapsulation

```mermaid
graph LR
  Ethernet["Ethernet"] --> IP["IP"] --> TCP["TCP (port 3260)"] --> iSCSI["iSCSI PDU"] --> SCSI["SCSI CDB / Data"]
```

## Standards

| Document | Title |
|----------|-------|
| [RFC 7143](https://www.rfc-editor.org/rfc/rfc7143) | Internet Small Computer System Interface (iSCSI) Protocol (consolidated) |
| [RFC 7144](https://www.rfc-editor.org/rfc/rfc7144) | iSCSI SCSI Features Update |
| [RFC 4171](https://www.rfc-editor.org/rfc/rfc4171) | iSNS — Internet Storage Name Service |
| [RFC 3723](https://www.rfc-editor.org/rfc/rfc3723) | Securing Block Storage Protocols over IP (IPsec for iSCSI) |
| [RFC 3720](https://www.rfc-editor.org/rfc/rfc3720) | iSCSI (original specification, obsoleted by RFC 7143) |

## See Also

- [Fibre Channel](fibrechannel.md) — dedicated storage fabric protocol
- [NVMe-oF](nvmeof.md) — NVMe over Fabrics (lower latency alternative)
- [RDMA](../hpc/rdma.md) — iSER (iSCSI Extensions for RDMA) runs iSCSI over RDMA
