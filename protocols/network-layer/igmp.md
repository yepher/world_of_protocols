# IGMP (Internet Group Management Protocol)

> **Standard:** [RFC 3376](https://www.rfc-editor.org/rfc/rfc3376) (IGMPv3) | **Layer:** Network (Layer 3) | **Wireshark filter:** `igmp`

IGMP manages multicast group membership between hosts and their local router. When a host wants to receive multicast traffic (e.g., IPTV, live streaming, stock feeds), it sends an IGMP report to join the multicast group. The local router uses this to decide which multicast streams to forward to the local subnet. IGMP operates between hosts and their first-hop router only — multicast routing between routers uses PIM.

## IGMPv3 Message

```mermaid
packet-beta
  0-7: "Type"
  8-15: "Max Resp Code"
  16-31: "Checksum"
  32-63: "Group Address"
```

## Message Types

| Type | Name | Direction | Description |
|------|------|-----------|-------------|
| 0x11 | Membership Query | Router → Hosts | Ask which groups hosts are subscribed to |
| 0x16 | Membership Report (v2) | Host → Router | Report group membership |
| 0x22 | Membership Report (v3) | Host → Router | Report with source filtering |
| 0x17 | Leave Group (v2) | Host → Router | Leave a multicast group |

## IGMPv3 Report

```mermaid
packet-beta
  0-7: "Type (0x22)"
  8-15: "Reserved"
  16-31: "Checksum"
  32-47: "Reserved"
  48-63: "Number of Group Records"
  64-95: "Group Record 1 ..."
  96-127: "Group Record N ..."
```

### Group Record

| Field | Size | Description |
|-------|------|-------------|
| Record Type | 8 bits | MODE_IS_INCLUDE, MODE_IS_EXCLUDE, etc. |
| Aux Data Len | 8 bits | Length of auxiliary data (usually 0) |
| Number of Sources | 16 bits | Source addresses for source-specific multicast |
| Multicast Address | 32 bits | Group being joined/left |
| Source Addresses | 32 bits each | Sources to include or exclude |

## Join/Leave Flow

```mermaid
sequenceDiagram
  participant H as Host
  participant R as Router

  R->>H: General Query (dst: 224.0.0.1, "who's listening?")
  H->>R: Membership Report (group 239.1.1.1, dst: 224.0.0.22)
  Note over R: Router forwards multicast for 239.1.1.1 to this subnet

  Note over H: Host wants to leave
  H->>R: Leave Group (group 239.1.1.1, dst: 224.0.0.2)
  R->>H: Group-Specific Query (group 239.1.1.1)
  Note over R: No other members respond — stop forwarding
```

## IGMP Snooping

Layer 2 switches examine IGMP messages to learn which ports need multicast traffic, preventing unnecessary flooding to all ports:

```mermaid
graph TD
  Router["Router"] --> Switch["Switch (IGMP snooping)"]
  Switch -->|"239.1.1.1"| Port1["Port 1 (joined)"]
  Switch -->|"239.1.1.1"| Port3["Port 3 (joined)"]
  Switch -.-x Port2["Port 2 (not joined)"]
```

## Multicast Address Ranges

| Range | Scope | Description |
|-------|-------|-------------|
| 224.0.0.0/24 | Link-local | IGMP, OSPF, VRRP (not forwarded by routers) |
| 224.0.0.1 | Link-local | All hosts |
| 224.0.0.2 | Link-local | All routers |
| 224.0.0.22 | Link-local | IGMPv3 reports |
| 224.0.1.0/24 | Internetwork | NTP, SLP, etc. |
| 239.0.0.0/8 | Administratively scoped | Private multicast (like RFC 1918 for unicast) |

## Encapsulation

```mermaid
graph LR
  IP2["IPv4 (Protocol 2)"] --> IGMP2["IGMP"]
```

IGMP is carried directly in IP packets with protocol number 2 and TTL=1.

## Standards

| Document | Title |
|----------|-------|
| [RFC 3376](https://www.rfc-editor.org/rfc/rfc3376) | IGMPv3 |
| [RFC 2236](https://www.rfc-editor.org/rfc/rfc2236) | IGMPv2 |
| [RFC 4541](https://www.rfc-editor.org/rfc/rfc4541) | IGMP and MLD Snooping Considerations |

## See Also

- [IPv4](ip.md) — IGMP is an IPv4 protocol
- [OSPF](ospf.md) — uses multicast 224.0.0.5/6
- [VRRP](vrrp.md) — uses multicast 224.0.0.18
