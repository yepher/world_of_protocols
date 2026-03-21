# SMPTE ST 2022 (Professional Video over IP)

> **Standard:** [SMPTE ST 2022](https://www.smpte.org/standards/st2022) | **Layer:** Application (Layer 7) | **Wireshark filter:** `smpte_2022` or `rtp`

SMPTE ST 2022 is a suite of standards for transporting professional video over IP networks, developed as the broadcast industry's first standardized approach to replacing SDI with IP. It covers MPEG transport streams, uncompressed SDI mapping, forward error correction (FEC), and seamless network redundancy. While ST 2110 has largely superseded ST 2022 for new facility designs, ST 2022-7 (seamless protection switching) remains fundamental to ST 2110 deployments, and ST 2022-6 (uncompressed SDI over IP) is still found in many operational broadcast facilities.

## Suite of Standards

| Standard | Title | Description |
|----------|-------|-------------|
| ST 2022-1 | FEC for MPEG-TS | Forward Error Correction for MPEG transport streams |
| ST 2022-2 | Unidirectional MPEG-TS over IP | Constant bitrate MPEG-TS in UDP/RTP |
| ST 2022-5 | FEC for High Bitrate Media | FEC for uncompressed and high-bitrate streams |
| ST 2022-6 | Uncompressed SDI over IP | Maps entire SDI signal into RTP (HBRMT) |
| ST 2022-7 | Seamless Protection Switching | Dual-path hitless redundancy for any RTP stream |

## Forward Error Correction (ST 2022-1 / ST 2022-5)

ST 2022-1 defines a 2D FEC scheme based on Pro-MPEG CoP3 that recovers lost packets without retransmission. Media packets are arranged in a matrix, and XOR-based FEC packets are generated for each column and row:

```mermaid
packet-beta
  0-7: "SNBase low (16)"
  8-15: "Length Recovery"
  16-16: "E"
  17-23: "PT Recovery"
  24-31: "Mask"
  32-55: "TS Recovery"
  56-63: "SNBase ext (8)"
  64-79: "Offset"
  80-87: "NA"
  88-95: "D/Type"
  96-111: "Index"
  112-127: "FEC Payload ..."
```

### FEC Key Fields

| Field | Size | Description |
|-------|------|-------------|
| SNBase | 24 bits | Base sequence number of protected packets |
| Length Recovery | 16 bits | XOR of payload lengths of protected packets |
| E (Extension) | 1 bit | RTP header extension recovery |
| PT Recovery | 7 bits | XOR of payload type fields |
| Mask | 8 bits | Bitmask identifying protected packets |
| TS Recovery | 24 bits | XOR of timestamps of protected packets |
| Offset | 16 bits | Column spacing in the FEC matrix |
| NA | 8 bits | Number of media packets per FEC group |
| D | 1 bit | Direction: 0 = column FEC, 1 = row FEC |
| Index | 16 bits | FEC packet index within the group |

### FEC Matrix

The 2D FEC matrix arranges media packets in rows and columns. Column FEC protects against burst loss; row FEC protects against random loss:

```mermaid
graph TD
  subgraph "FEC Matrix (L columns x D rows)"
    P1["Pkt 1"] --- P2["Pkt 2"] --- P3["Pkt 3"] --- P4["Pkt 4"] --- P5["Pkt 5"]
    P6["Pkt 6"] --- P7["Pkt 7"] --- P8["Pkt 8"] --- P9["Pkt 9"] --- P10["Pkt 10"]
    P11["Pkt 11"] --- P12["Pkt 12"] --- P13["Pkt 13"] --- P14["Pkt 14"] --- P15["Pkt 15"]
  end

  P5 --> RF1["Row FEC 1"]
  P10 --> RF2["Row FEC 2"]
  P15 --> RF3["Row FEC 3"]

  P11 --> CF1["Col FEC 1"]
  P12 --> CF2["Col FEC 2"]
  P13 --> CF3["Col FEC 3"]
  P14 --> CF4["Col FEC 4"]
  P15 --> CF5["Col FEC 5"]
```

### FEC Parameters

| Parameter | Symbol | Description |
|-----------|--------|-------------|
| Columns | L | Number of packets per row (1-20) |
| Rows | D | Number of packets per column (4-20) |
| Column FEC | | Recovers from burst loss up to L consecutive packets |
| Row FEC | | Recovers from random single-packet loss per row |
| 2D Recovery | | Can recover multiple losses using both dimensions |
| Overhead | | 1/L + 1/D (e.g., L=10, D=10: 20% overhead) |

## MPEG Transport Stream over IP (ST 2022-2)

ST 2022-2 defines the carriage of MPEG-2 transport streams over IP. Each RTP packet carries 7 TS packets (7 x 188 = 1316 bytes) for a standard MTU:

```mermaid
packet-beta
  0-31: "RTP Header (12 bytes) ..."
  32-63: "... RTP Header continued ..."
  64-95: "... RTP Header (last 32 bits)"
  96-127: "TS Packet 1 (188 bytes) ..."
  128-159: "... TS Packets 2-6 ..."
  160-191: "TS Packet 7 (188 bytes) ..."
```

| Parameter | Value |
|-----------|-------|
| RTP payload type | Dynamic (negotiated via SDP) |
| Clock rate | 90 kHz |
| TS packets per RTP | 7 (typical, for 1316-byte payload) |
| Transport | UDP unicast or multicast |
| FEC | ST 2022-1 (optional but recommended) |

## Uncompressed SDI over IP (ST 2022-6)

ST 2022-6 maps an entire SDI signal (including blanking, embedded audio, and ancillary data) directly into RTP using the High Bitrate Media Transport (HBRMT) payload format:

### HBRMT Payload Header

```mermaid
packet-beta
  0-1: "V"
  2: "CF"
  3-7: "Reserved"
  8-11: "MAP"
  12-15: "FRCount"
  16-23: "R"
  24-31: "Ext. (F/VSID/FRCount)"
```

### HBRMT Key Fields

| Field | Size | Description |
|-------|------|-------------|
| V (Version) | 2 bits | HBRMT version (0) |
| CF (Clock Frequency) | 1 bit | 0 = not locked, 1 = locked to reference |
| MAP | 4 bits | SDI mapping mode (identifies signal format) |
| FRCount | 8 bits | Frame count (wrapping counter for frame tracking) |
| R | 8 bits | Reference for timing reconstruction |

### MAP Values (SDI Formats)

| MAP | SDI Standard | Data Rate | Description |
|-----|-------------|-----------|-------------|
| 0 | ST 259 (SD-SDI) | 270 Mbps | Standard definition |
| 1 | ST 292-1 (HD-SDI) | 1.485 Gbps | High definition |
| 2 | ST 425-1 (3G-SDI) A | 2.97 Gbps | 3G Level A |
| 3 | ST 425-1 (3G-SDI) B-DL | 2.97 Gbps | 3G Level B (dual-link) |
| 4 | ST 2081-10 (6G-SDI) | 5.94 Gbps | 6G single-link |
| 5 | ST 2082-10 (12G-SDI) | 11.88 Gbps | 12G single-link |

## Seamless Protection Switching (ST 2022-7)

ST 2022-7 provides hitless redundancy by transmitting identical RTP streams over two physically separate network paths. The receiver reconstructs a single clean output by selecting the first-arriving copy of each packet:

```mermaid
sequenceDiagram
  participant S as Sender
  participant NA as Network Path A
  participant NB as Network Path B
  participant R as Receiver (ST 2022-7)

  S->>NA: RTP stream (seq 100, 101, 102, ...)
  S->>NB: RTP stream (seq 100, 101, 102, ...)

  Note over NA: Packet 101 lost on Path A
  NA->>R: seq 100, -, 102
  NB->>R: seq 100, 101, 102

  Note over R: Merge: use Path B copy of seq 101
  R->>R: Output: 100, 101, 102 (seamless)
```

### ST 2022-7 Architecture

```mermaid
graph TD
  subgraph Sender
    S["Source"] --> S_A["NIC A"]
    S --> S_B["NIC B"]
  end
  subgraph "Network Fabric"
    S_A --> SW_A["Switch Fabric A (Blue)"]
    S_B --> SW_B["Switch Fabric B (Red)"]
  end
  subgraph Receiver
    SW_A --> R_A["NIC A"]
    SW_B --> R_B["NIC B"]
    R_A --> Merge["ST 2022-7 Merge"]
    R_B --> Merge
    Merge --> Out["Clean Output"]
  end
```

### ST 2022-7 Parameters

| Parameter | Value |
|-----------|-------|
| Path difference tolerance | Configurable (typically up to 450 ms) |
| Buffer depth | Must accommodate max path differential |
| Packet matching | By RTP sequence number |
| Failover time | Zero (hitless, no frame loss) |
| Scope | Per-flow (each RTP stream independently protected) |
| Applicable protocols | Any RTP stream (ST 2022-6, ST 2110, AES67, etc.) |

## ST 2022 vs ST 2110

| Feature | SMPTE ST 2022-6 | SMPTE ST 2110 |
|---------|-----------------|---------------|
| Video mapping | Entire SDI signal (active + blanking) | Active video pixels only |
| Audio | Embedded in SDI stream | Separate audio flow (ST 2110-30) |
| Ancillary data | Embedded in SDI stream | Separate data flow (ST 2110-40) |
| Bandwidth (1080i) | ~1.5 Gbps (full SDI rate) | ~1.3 Gbps (active video only) |
| Essence routing | All-or-nothing (single flow) | Independent per-essence routing |
| Synchronization | PTP (ST 2059) | PTP (ST 2059) |
| Multicast | Supported | Required |
| Compression | No (raw SDI mapping) | Optional (ST 2110-22: JPEG XS) |
| Redundancy | ST 2022-7 | ST 2022-7 |
| SDP | One SDP per SDI signal | One SDP per essence flow |
| Ideal use | SDI migration, simple installations | New IP-native facility builds |

## Encapsulation

```mermaid
graph LR
  IP["IP (Unicast/Multicast)"] --> UDP["UDP"]
  UDP --> RTP["RTP"]
  RTP --> TS["MPEG-TS (ST 2022-2)"]
  RTP --> SDI["SDI Mapping (ST 2022-6)"]
  RTP --> FEC["FEC Packets (ST 2022-1/5)"]
```

## Standards

| Document | Title |
|----------|-------|
| [SMPTE ST 2022-1](https://www.smpte.org/standards/st2022) | Forward Error Correction for MPEG-2 TS over IP |
| [SMPTE ST 2022-2](https://www.smpte.org/standards/st2022) | Unidirectional Transport of Constant Bit Rate MPEG-2 TS over IP |
| [SMPTE ST 2022-5](https://www.smpte.org/standards/st2022) | Forward Error Correction for High Bit Rate Media Transport over IP |
| [SMPTE ST 2022-6](https://www.smpte.org/standards/st2022) | High Bit Rate Media Transport over IP (HBRMT) |
| [SMPTE ST 2022-7](https://www.smpte.org/standards/st2022) | Seamless Protection Switching of RTP Datagrams |
| [SMPTE ST 2059-2](https://www.smpte.org/standards/st2059) | SMPTE Profile for Use of IEEE-1588 PTP |
| [Pro-MPEG CoP3](https://tech.ebu.ch/docs/tech/tech3348.pdf) | Code of Practice #3: FEC framework (basis for ST 2022-1) |

## See Also

- [SMPTE ST 2110](smpte2110.md) -- successor suite for professional media over IP
- [NDI](ndi.md) -- alternative IP video protocol for production
- [RTP](../voip/rtp.md) -- underlying transport protocol for all ST 2022 media
- [SDP](../voip/sdp.md) -- session description for ST 2022 flows
- [NTP](../naming/ntp.md) -- time synchronization (PTP is a related precision protocol)
