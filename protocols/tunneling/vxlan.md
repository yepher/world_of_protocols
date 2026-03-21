# VXLAN (Virtual Extensible LAN)

> **Standard:** [RFC 7348](https://www.rfc-editor.org/rfc/rfc7348) | **Layer:** Data Link / Tunneling (Layer 2 over Layer 3) | **Wireshark filter:** `vxlan`

VXLAN is an overlay tunneling protocol that encapsulates Layer 2 Ethernet frames within UDP/IP packets, allowing Layer 2 networks to be extended across Layer 3 boundaries. It was designed to solve the scalability limitations of VLANs (4094 IDs) in large data centers by providing a 24-bit segment ID space (over 16 million virtual networks). VXLAN is the dominant overlay protocol in modern data center fabrics and cloud networking, used by VMware NSX, Linux bridges, Cisco ACI, and most cloud providers.

## Packet Format

```mermaid
packet-beta
  0-7: "VXLAN Flags"
  8-31: "Reserved (24 bits)"
  32-55: "VNI (24 bits)"
  56-63: "Reserved (8 bits)"
```

The 8-byte VXLAN header encapsulates a complete inner Ethernet frame:

### Full Encapsulation Stack

```mermaid
packet-beta
  0-31: "Outer Ethernet Header (14 bytes)"
  32-63: "Outer IP Header (20 bytes)"
  64-79: "Outer UDP Header (8 bytes)"
  80-95: "VXLAN Header (8 bytes)"
  96-127: "Inner Ethernet Frame (original) ..."
  128-159: "Outer FCS"
```

## Key Fields

| Field | Size | Description |
|-------|------|-------------|
| Flags | 8 bits | Bit 3 (I flag) must be 1; indicates valid VNI |
| Reserved | 24 bits | Must be zero |
| VNI | 24 bits | VXLAN Network Identifier (0 - 16,777,215) |
| Reserved | 8 bits | Must be zero |

### Flags Detail

```mermaid
packet-beta
  0-2: "R R R"
  3: "I"
  4-7: "R R R R"
```

Only the **I flag** (bit 3) is defined. When set to 1, the VNI field is valid. All other bits are reserved and set to 0.

## Outer UDP Header

| Field | Value | Description |
|-------|-------|-------------|
| Source Port | Hash-based | Hash of inner frame headers (for ECMP load balancing) |
| Destination Port | 4789 | IANA-assigned VXLAN port |
| Length | Variable | UDP length including VXLAN header and inner frame |
| Checksum | 0 or computed | Often set to 0 (inner frame has its own FCS) |

The source port is derived from a hash of the inner frame's headers (src/dst MAC, IP, L4 ports), ensuring that flows between the same endpoints take the same path while different flows are distributed across ECMP paths.

## How VXLAN Works

```mermaid
graph TD
  subgraph "Rack 1"
    VM1["VM A<br/>(10.0.1.10)"] --> VTEP1["VTEP 1<br/>(192.168.1.1)"]
  end

  subgraph "Rack 2"
    VM2["VM B<br/>(10.0.1.20)"] --> VTEP2["VTEP 2<br/>(192.168.2.1)"]
  end

  VTEP1 -->|"VXLAN tunnel<br/>(VNI 5000)<br/>over IP fabric"| VTEP2
```

| Term | Description |
|------|-------------|
| VTEP | VXLAN Tunnel Endpoint — encapsulates/decapsulates VXLAN |
| VNI | VXLAN Network Identifier — isolates virtual networks (like VLAN ID but 24-bit) |
| Underlay | Physical IP network connecting VTEPs |
| Overlay | Virtual L2 network carried inside VXLAN |

### Traffic Flow

```mermaid
sequenceDiagram
  participant A as VM A (10.0.1.10)
  participant VTEP1 as VTEP 1
  participant VTEP2 as VTEP 2
  participant B as VM B (10.0.1.20)

  A->>VTEP1: Ethernet frame (dst MAC = B)
  Note over VTEP1: Lookup: B's MAC → VTEP2 (192.168.2.1), VNI 5000
  VTEP1->>VTEP2: Outer IP + UDP 4789 + VXLAN(VNI=5000) + original frame
  Note over VTEP2: Decapsulate, deliver to local port for VNI 5000
  VTEP2->>B: Original Ethernet frame
```

## MAC Learning

VTEPs learn remote MAC-to-VTEP mappings through:

| Method | Description |
|--------|-------------|
| Data plane learning | Inspect source MAC of received VXLAN packets (flood-and-learn) |
| Multicast | Unknown unicast/broadcast/multicast flooded via IP multicast group per VNI |
| EVPN (BGP) | Control plane distributes MAC/IP→VTEP mappings (no flooding needed) |
| Static | Manual VTEP-MAC configuration |

EVPN ([RFC 7432](https://www.rfc-editor.org/rfc/rfc7432)) is the modern preferred approach — it eliminates flooding and provides efficient ARP suppression.

## VXLAN vs VLAN

| Feature | VLAN (802.1Q) | VXLAN |
|---------|---------------|-------|
| ID space | 12 bits (4,094) | 24 bits (16,777,216) |
| Scope | Single L2 domain | Across L3 boundaries |
| Encapsulation | 4-byte tag in Ethernet header | Full UDP/IP encapsulation |
| Scalability | Limited by STP, MAC table size | Data center scale |
| Multi-tenancy | Limited | Native (millions of segments) |
| MTU overhead | 4 bytes | 50 bytes (requires jumbo frames) |

## MTU Considerations

VXLAN adds 50 bytes of overhead:

| Component | Size |
|-----------|------|
| Outer Ethernet | 14 bytes |
| Outer IP | 20 bytes |
| Outer UDP | 8 bytes |
| VXLAN header | 8 bytes |
| **Total overhead** | **50 bytes** |

With a standard 1500-byte MTU, the inner frame MTU is 1450 bytes. Most data center fabrics use **jumbo frames (9000+ byte MTU)** on the underlay to avoid fragmentation.

## VXLAN-GPE (Generic Protocol Extension)

[RFC 8926](https://www.rfc-editor.org/rfc/rfc8926) extends VXLAN with a Next Protocol field, allowing encapsulation of non-Ethernet payloads (IPv4, IPv6, NSH).

## Encapsulation

```mermaid
graph LR
  OuterETH["Outer Ethernet"] --> OuterIP["Outer IP"] --> UDP4789["UDP 4789"] --> VXLAN["VXLAN Header"]
  VXLAN --> InnerETH["Inner Ethernet Frame"]
  InnerETH --> InnerIP["Inner IP"]
```

## Standards

| Document | Title |
|----------|-------|
| [RFC 7348](https://www.rfc-editor.org/rfc/rfc7348) | Virtual eXtensible Local Area Network (VXLAN) |
| [RFC 8365](https://www.rfc-editor.org/rfc/rfc8365) | A Network Virtualization Overlay Solution Using EVPN |
| [RFC 7432](https://www.rfc-editor.org/rfc/rfc7432) | BGP MPLS-Based Ethernet VPN (EVPN) |
| [RFC 8926](https://www.rfc-editor.org/rfc/rfc8926) | Geneve — Generic Network Virtualization Encapsulation |

## See Also

- [Ethernet](../link-layer/ethernet.md) — the inner frames VXLAN encapsulates
- [UDP](../transport-layer/udp.md) — VXLAN transport
- [GRE](../network-layer/gre.md) — alternative tunneling protocol
- [L2TP](l2tp.md) — another L2 tunneling protocol
- [MPLS](../network-layer/mpls.md) — carrier-grade L2/L3 VPN alternative
- [BGP](../routing/bgp.md) — EVPN control plane for VXLAN
