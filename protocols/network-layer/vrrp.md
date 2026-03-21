# VRRP (Virtual Router Redundancy Protocol)

> **Standard:** [RFC 5798](https://www.rfc-editor.org/rfc/rfc5798) | **Layer:** Network (Layer 3) | **Wireshark filter:** `vrrp`

VRRP provides automatic default gateway failover for hosts on a LAN. Two or more routers share a virtual IP address and a virtual MAC address. One router is elected Master and handles all traffic to the virtual IP; the others are Backups that take over within seconds if the Master fails. VRRP is essential for high-availability network designs — virtually every enterprise and data center network uses it (or Cisco's proprietary HSRP) for gateway redundancy.

## Packet

```mermaid
packet-beta
  0-3: "Version (3)"
  4-7: "Type (1)"
  8-15: "Virtual Router ID"
  16-23: "Priority"
  24-31: "Count IP Addrs"
  32-35: "Reserved"
  36-47: "Max Advert Interval (12 bits)"
  48-63: "Checksum"
  64-95: "IP Address 1 (virtual IP)"
  96-127: "IP Address N ..."
```

## Key Fields

| Field | Size | Description |
|-------|------|-------------|
| Version | 4 bits | VRRP version (3 for VRRPv3) |
| Type | 4 bits | 1 = Advertisement (only type defined) |
| VRID | 8 bits | Virtual Router ID (1-255) — identifies the VRRP group |
| Priority | 8 bits | 1-254 (higher = more preferred); 255 = IP address owner |
| Count IP Addrs | 8 bits | Number of virtual IP addresses |
| Max Advert Interval | 12 bits | Centiseconds between advertisements (default 100 = 1 second) |
| Checksum | 16 bits | Checksum over the VRRP packet |
| IP Addresses | 32 bits each | The virtual IP address(es) this VRID protects |

## How VRRP Works

```mermaid
graph TD
  subgraph LAN
    Host1["Host<br/>GW: 10.0.0.1"]
    Host2["Host<br/>GW: 10.0.0.1"]
  end
  subgraph VRRP Group
    R1["Router A (Master)<br/>Real: 10.0.0.2<br/>Priority: 200"]
    R2["Router B (Backup)<br/>Real: 10.0.0.3<br/>Priority: 100"]
    VIP["Virtual IP: 10.0.0.1<br/>Virtual MAC: 00-00-5E-00-01-{VRID}"]
  end
  Host1 --> VIP
  Host2 --> VIP
  VIP --> R1
  VIP -.->|failover| R2
```

### Election and Failover

```mermaid
sequenceDiagram
  participant A as Router A (Priority 200)
  participant B as Router B (Priority 100)
  participant LAN as LAN (Hosts)

  Note over A,B: Both start, exchange advertisements
  A->>LAN: VRRP Advertisement (VRID=1, priority=200)
  Note over B: A has higher priority → B becomes Backup
  A->>LAN: Gratuitous ARP (virtual IP → virtual MAC)
  Note over LAN: Hosts send traffic to virtual MAC

  Note over A: Router A fails!
  Note over B: No advertisement received for 3+ intervals
  B->>LAN: VRRP Advertisement (VRID=1, priority=100)
  B->>LAN: Gratuitous ARP (virtual IP → virtual MAC)
  Note over LAN: Failover complete (~3 seconds)
```

## Priority

| Priority | Meaning |
|----------|---------|
| 255 | Router owns the virtual IP (IP address is configured on this router's interface) |
| 101-254 | High priority (manually configured) |
| 100 | Default priority |
| 1-99 | Low priority |
| 0 | Master is shutting down (triggers immediate failover) |

## Virtual MAC Address

VRRP uses a well-known MAC address based on the VRID:

| IP Version | Virtual MAC Format |
|------------|-------------------|
| IPv4 | `00-00-5E-00-01-{VRID}` |
| IPv6 | `00-00-5E-00-02-{VRID}` |

This ensures that the MAC doesn't change during failover — hosts don't need to update their ARP caches.

## Preemption

When a higher-priority router recovers, it can preempt the current Master:

| Setting | Behavior |
|---------|----------|
| Preempt (default) | Higher-priority router takes over immediately |
| No-preempt | Current Master keeps the role until it fails |

## VRRP vs HSRP

| Feature | VRRP | HSRP (Cisco) |
|---------|------|------|
| Standard | IETF (RFC 5798) | Cisco proprietary |
| Default priority | 100 | 100 |
| Timers | Advertise: 1s, holddown: ~3s | Hello: 3s, holddown: 10s |
| Multicast | 224.0.0.18 (IPv4), ff02::12 (IPv6) | 224.0.0.2 (v1), 224.0.0.102 (v2) |
| Virtual MAC | 00-00-5E-00-01-xx | 00-00-0C-07-AC-xx |
| IP owner | Supported (priority 255) | Not supported |
| IPv6 | Native (VRRPv3) | HSRPv2 |

## Encapsulation

```mermaid
graph LR
  IP112["IPv4 (Protocol 112)"] --> VRRP2["VRRP"]
```

VRRP is carried directly in IP packets with protocol number 112, TTL=255, sent to multicast address `224.0.0.18`.

## Standards

| Document | Title |
|----------|-------|
| [RFC 5798](https://www.rfc-editor.org/rfc/rfc5798) | Virtual Router Redundancy Protocol (VRRP) Version 3 |
| [RFC 3768](https://www.rfc-editor.org/rfc/rfc3768) | VRRP Version 2 (IPv4 only) |

## See Also

- [IPv4](ip.md)
- [ARP](../link-layer/arp.md) — gratuitous ARP used during failover
- [OSPF](ospf.md) — routing protocol often used alongside VRRP
- [IGMP](igmp.md) — VRRP uses multicast 224.0.0.18
