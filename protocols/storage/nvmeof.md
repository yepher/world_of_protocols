# NVMe-oF (NVMe over Fabrics)

> **Standard:** [NVMe over Fabrics 1.1 (nvmexpress.org)](https://nvmexpress.org/specifications/) | **Layer:** Application / Transport | **Wireshark filter:** `nvme`

NVMe over Fabrics extends the NVMe protocol beyond a single machine's PCIe bus, allowing hosts to access remote NVMe storage over a network fabric. NVMe-oF preserves the high-parallelism, low-latency architecture of local NVMe — with up to 65,535 I/O queues each supporting 65,536 outstanding commands — while transporting commands and data over RDMA (RoCE v2, InfiniBand), TCP, or Fibre Channel. The result is significantly lower latency and higher IOPS than iSCSI for disaggregated storage.

## NVMe Architecture (Local vs Fabric)

```mermaid
graph LR
  subgraph "Local NVMe (PCIe)"
    Host1["Host CPU"] -->|"PCIe TLP"| SSD1["NVMe SSD"]
  end

  subgraph "NVMe over Fabrics"
    Host2["Host CPU"] -->|"NVMe-oF capsule"| RNIC["NIC / HBA"]
    RNIC -->|"RDMA / TCP / FC"| Fabric["Network Fabric"]
    Fabric --> TNIC["Target NIC / HBA"]
    TNIC --> SSD2["NVMe SSD(s)"]
  end
```

## Capsule Structure

NVMe-oF uses capsules to carry NVMe commands, responses, and data over a fabric:

### Command Capsule

```mermaid
packet-beta
  0-31: "Opcode (8) | Flags (8) | Command ID (16)"
  32-63: "NSID (Namespace ID, 32 bits)"
  64-127: "Reserved (64 bits)"
  128-191: "Metadata Pointer (64 bits)"
  192-319: "PRP / SGL (Data Pointer, 128 bits)"
  320-511: "Command Specific (192 bits)"
```

### Response Capsule (Completion Queue Entry)

```mermaid
packet-beta
  0-31: "Command Specific (32)"
  32-63: "Reserved (32)"
  64-79: "SQ Head Pointer (16)"
  80-95: "SQ Identifier (16)"
  96-111: "Command ID (16)"
  112-112: "P"
  113-127: "Status (15 bits)"
```

## Key Fields

| Field | Size | Description |
|-------|------|-------------|
| Opcode | 8 bits | NVMe command opcode (Read=0x02, Write=0x01, Identify=0x06) |
| Flags | 8 bits | Fused operation, PRP/SGL type |
| Command ID | 16 bits | Unique tag for matching completions to commands |
| NSID | 32 bits | Namespace ID — identifies the storage volume |
| SGL | 128 bits | Scatter-Gather List — describes data buffer locations |
| SQ Head Pointer | 16 bits | Submission Queue head — flow control |
| Status | 15 bits | Completion status (success, error codes) |
| P (Phase) | 1 bit | Phase tag — toggled to indicate new completion |

## NVMe-oF Transports

### Transport Binding Summary

| Transport | Port | Encapsulation | Latency | Requires |
|-----------|------|---------------|---------|----------|
| RDMA (RoCE v2) | 4420 | NVMe capsule in RDMA Send/Write | 10-30 us | Lossless Ethernet (DCB) or RoCE resilience |
| RDMA (InfiniBand) | 4420 | NVMe capsule in IB verbs | 5-15 us | InfiniBand fabric |
| TCP | 4420 | NVMe/TCP PDU over TCP | 50-200 us | Standard Ethernet |
| FC (FC-NVMe) | N/A | NVMe capsule in FC frames | 20-50 us | FC fabric (32G/64G) |

### NVMe/TCP PDU Header

```mermaid
packet-beta
  0-7: "PDU Type (8)"
  8-15: "Flags (8)"
  16-23: "Header Length (8)"
  24-31: "PDU Data Offset (8)"
  32-63: "PDU Length (32)"
```

| PDU Type | Value | Description |
|----------|-------|-------------|
| ICReq | 0x00 | Initialize Connection Request |
| ICResp | 0x01 | Initialize Connection Response |
| H2CData | 0x02 | Host-to-Controller Data |
| C2HData | 0x03 | Controller-to-Host Data |
| CapsuleCmd | 0x04 | Command Capsule |
| CapsuleResp | 0x05 | Response Capsule |
| H2CTermReq | 0x06 | Host-to-Controller Terminate Request |
| C2HTermReq | 0x07 | Controller-to-Host Terminate Request |
| R2T | 0x09 | Ready to Transfer |

## Submission Queue / Completion Queue Model

```mermaid
sequenceDiagram
  participant App as Host Application
  participant SQ as Submission Queue
  participant CQ as Completion Queue
  participant Ctrl as NVMe Controller (Remote)

  App->>SQ: Post NVMe command (SQ Tail++)
  App->>Ctrl: Ring SQ Doorbell
  Ctrl->>SQ: Fetch command (SQ Head++)
  Note over Ctrl: Execute I/O on NVMe SSD
  Ctrl->>CQ: Post completion entry (CQ Tail++)
  Ctrl->>App: Interrupt / MSI-X
  App->>CQ: Read completion (CQ Head++)
  App->>Ctrl: Ring CQ Doorbell
```

### Queue Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Admin Queue | 1 pair | Queue pair 0 — for management commands |
| I/O Queues | Up to 65,535 | One per CPU core is typical |
| Queue Depth | Up to 65,536 | Outstanding commands per queue |
| Total Commands | ~4 billion | 65,535 queues x 65,536 depth |

## Discovery Service

NVMe-oF provides a centralized Discovery Controller for locating storage targets:

```mermaid
sequenceDiagram
  participant H as Host
  participant D as Discovery Controller (port 8009)
  participant T as Storage Target (port 4420)

  H->>D: Connect to well-known Discovery NQN
  D->>H: Identify Controller (discovery type)
  H->>D: Get Log Page (Discovery Log)
  D->>H: Discovery Log Entries (subsystem NQN, transport, address, port)
  H->>D: Disconnect

  H->>T: Connect to storage subsystem NQN (port 4420)
  T->>H: Identify Controller, Identify Namespace
  Note over H,T: I/O commands (Read, Write, Flush)
```

### NVMe Qualified Name (NQN)

Format: `nqn.YYYY-MM.reversed.domain:identifier`

| Well-Known NQN | Purpose |
|----------------|---------|
| `nqn.2014-08.org.nvmexpress.discovery` | Discovery Controller |
| `nqn.2014-08.org.nvmexpress:uuid:<UUID>` | UUID-based naming |

## NVMe-oF over RDMA Flow

```mermaid
sequenceDiagram
  participant H as Host (Initiator)
  participant T as Target (Controller)

  Note over H,T: Connection Setup (RDMA)
  H->>T: RDMA Connect (NVMe Fabric Connect command)
  T->>H: RDMA Accept + Connect Response
  H->>T: Identify Controller
  T->>H: Controller data (model, capacity, queue limits)

  Note over H,T: I/O (RDMA one-sided)
  H->>T: RDMA Send (NVMe Read command capsule)
  T->>H: RDMA Write (data directly to host memory)
  T->>H: RDMA Send (Completion capsule)
```

## Performance Comparison

| Metric | iSCSI | NVMe/TCP | NVMe/RDMA | NVMe/FC |
|--------|-------|----------|-----------|---------|
| Latency | 100-500 us | 50-200 us | 10-30 us | 20-50 us |
| IOPS (per target) | ~200K | ~500K | ~1M+ | ~800K |
| CPU Overhead | High (TCP + iSCSI + SCSI) | Medium (TCP + NVMe) | Very low (kernel bypass) | Low |
| Queue Depth | ~256 typical | 65K queues x 65K | 65K queues x 65K | 65K queues x 65K |
| Multi-queue | Limited | Yes (per-core) | Yes (per-core) | Yes (per-core) |

## Encapsulation (TCP Transport)

```mermaid
graph LR
  Ethernet["Ethernet"] --> IP["IP"] --> TCP["TCP (port 4420)"] --> NVMeTCP["NVMe/TCP PDU"] --> NVMe["NVMe Capsule"]
```

## Encapsulation (RDMA Transport)

```mermaid
graph LR
  Ethernet["Ethernet"] --> IP["IP"] --> UDP["UDP (port 4791)"] --> IB["InfiniBand BTH"] --> NVMe["NVMe Capsule"]
```

## Standards

| Document | Title |
|----------|-------|
| [NVMe Base Spec 2.1](https://nvmexpress.org/specifications/) | NVM Express Base Specification |
| [NVMe-oF 1.1](https://nvmexpress.org/specifications/) | NVMe over Fabrics Specification |
| [NVMe/TCP Transport Binding](https://nvmexpress.org/specifications/) | TCP Transport Binding Specification |
| [RFC 7143](https://www.rfc-editor.org/rfc/rfc7143) | iSCSI (for comparison) |
| [INCITS FC-NVMe-2](https://www.t11.org/) | FC-NVMe Fibre Channel Transport |

## See Also

- [iSCSI](iscsi.md) — SCSI over TCP/IP (predecessor technology)
- [RDMA](../hpc/rdma.md) — transport substrate for NVMe/RDMA (RoCE, InfiniBand)
- [Fibre Channel](fibrechannel.md) — FC-NVMe transport
- [PCIe](../bus/pcie.md) — local NVMe transport (NVMe was designed for PCIe)
