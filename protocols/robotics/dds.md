# DDS / ROS 2 (Data Distribution Service)

> **Standard:** [OMG DDS v1.4](https://www.omg.org/spec/DDS/) / [RTPS v2.3](https://www.omg.org/spec/DDSI-RTPS/) | **Layer:** Application (Layer 7) | **Wireshark filter:** `rtps`

DDS (Data Distribution Service) is a middleware protocol for real-time, publish-subscribe data distribution. It is the default communication layer for **ROS 2** (Robot Operating System 2), the dominant framework for robotics software. DDS provides automatic peer discovery, strongly-typed topics, configurable Quality of Service (QoS), and decentralized architecture — no broker required. The wire protocol is RTPS (Real-Time Publish-Subscribe), which runs over UDP multicast for discovery and UDP unicast for data.

## Architecture

```mermaid
graph TD
  subgraph "ROS 2 Application"
    Node1["Node: /camera"]
    Node2["Node: /detector"]
    Node3["Node: /controller"]
  end

  subgraph "DDS Middleware"
    DP["Domain Participant"]
    DW1["DataWriter<br/>(Publisher)"]
    DR1["DataReader<br/>(Subscriber)"]
    Topic["Topic: /image_raw<br/>(sensor_msgs/Image)"]
  end

  Node1 --> DW1
  DW1 --> Topic
  Topic --> DR1
  DR1 --> Node2
  Node3 --> DR1
```

DDS is **brokerless** — publishers and subscribers discover each other directly using multicast, then communicate peer-to-peer.

## RTPS Wire Protocol

### RTPS Message

```mermaid
packet-beta
  0-31: "Protocol ('R' 'T' 'P' 'S')"
  32-47: "Version (2.3)"
  48-63: "Vendor ID"
  64-95: "GUID Prefix (96 bits) ..."
  96-127: "GUID Prefix continued"
  128-159: "GUID Prefix (last 32 bits)"
  160-191: "Submessage 1 ..."
  192-223: "Submessage 2 ..."
```

## Key Fields

| Field | Size | Description |
|-------|------|-------------|
| Protocol | 4 bytes | Magic bytes `RTPS` (0x52545053) |
| Version | 2 bytes | Protocol version (major.minor) |
| Vendor ID | 2 bytes | DDS implementation identifier |
| GUID Prefix | 12 bytes | Globally unique identifier for this participant |
| Submessages | Variable | One or more submessages (data, heartbeat, ack, etc.) |

### Submessage Header

```mermaid
packet-beta
  0-7: "Submessage ID"
  8-15: "Flags"
  16-31: "Octets to Next Header"
```

### Submessage Types

| ID | Name | Description |
|----|------|-------------|
| 0x01 | PAD | Padding |
| 0x06 | ACKNACK | Acknowledge/negative-acknowledge data |
| 0x07 | HEARTBEAT | Inform readers of available data sequence numbers |
| 0x09 | GAP | Indicate irrelevant sequence numbers |
| 0x12 | INFO_TS | Timestamp for subsequent submessages |
| 0x14 | INFO_SRC | Source participant info |
| 0x15 | DATA | User data payload |
| 0x16 | DATA_FRAG | Fragmented data |

## Discovery

DDS uses a two-phase discovery protocol:

### Simple Participant Discovery Protocol (SPDP)

Participants announce themselves via UDP multicast:

```mermaid
sequenceDiagram
  participant A as Participant A
  participant M as Multicast Group (239.255.0.1)
  participant B as Participant B

  A->>M: SPDP announcement (GUID, locators, QoS)
  B->>M: SPDP announcement (GUID, locators, QoS)
  Note over A,B: Both know about each other
```

| Parameter | Default Value |
|-----------|---------------|
| Discovery multicast group | 239.255.0.1 |
| Discovery port | 7400 + (250 × domain_id) + participant_id offsets |
| Announcement period | 30 seconds (default) |

### Simple Endpoint Discovery Protocol (SEDP)

After participants discover each other, they exchange their endpoints (DataWriters/DataReaders) via reliable unicast:

```mermaid
sequenceDiagram
  participant A as Participant A
  participant B as Participant B

  Note over A,B: SPDP: know each other exists
  A->>B: SEDP: "I have DataWriter for topic /cmd_vel"
  B->>A: SEDP: "I have DataReader for topic /cmd_vel"
  Note over A,B: Topic match! Begin data exchange
  A->>B: DATA submessages (unicast UDP)
```

## ROS 2 Integration

ROS 2 maps its concepts onto DDS:

| ROS 2 Concept | DDS Concept |
|---------------|-------------|
| Node | Domain Participant |
| Topic | Topic (with type) |
| Publisher | DataWriter |
| Subscriber | DataReader |
| Service | Request/Reply Topics (two topics) |
| Action | Multiple Topics (goal, result, feedback, status) |
| QoS Profile | DDS QoS policies |
| Domain ID | DDS Domain ID (network isolation) |

### ROS 2 Topic Wire Format

ROS 2 messages (e.g., `geometry_msgs/Twist`) are serialized using **CDR** (Common Data Representation) encoding and carried as RTPS DATA submessage payloads.

### Common ROS 2 DDS Implementations

| Implementation | Vendor | ROS 2 RMW |
|---------------|--------|-----------|
| Fast DDS | eProsima | rmw_fastrtps (default) |
| Cyclone DDS | Eclipse | rmw_cyclonedds |
| Connext DDS | RTI | rmw_connextdds |
| GurumDDS | Gurum Networks | rmw_gurumdds |

## Quality of Service (QoS)

DDS provides rich QoS policies — critical for robotics where some data needs reliability and some needs low latency:

| QoS Policy | Options | Description |
|------------|---------|-------------|
| Reliability | BEST_EFFORT, RELIABLE | Guaranteed delivery vs. lowest latency |
| Durability | VOLATILE, TRANSIENT_LOCAL, TRANSIENT, PERSISTENT | Whether late joiners receive historical data |
| History | KEEP_LAST(n), KEEP_ALL | How many samples to retain |
| Deadline | Duration | Maximum expected time between samples |
| Liveliness | AUTOMATIC, MANUAL | How to detect dead writers |
| Lifespan | Duration | How long data is valid |
| Ownership | SHARED, EXCLUSIVE | Multiple or single writer per topic instance |

### ROS 2 QoS Profiles

| Profile | Reliability | Durability | History | Use Case |
|---------|-------------|-----------|---------|----------|
| Sensor data | BEST_EFFORT | VOLATILE | KEEP_LAST(5) | Camera, LiDAR, IMU |
| Parameters | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) | Config parameters |
| Services | RELIABLE | VOLATILE | KEEP_ALL | Request-response |
| Default | RELIABLE | VOLATILE | KEEP_LAST(10) | General purpose |

## Encapsulation

```mermaid
graph LR
  UDP_M["UDP multicast (discovery)"] --> RTPS_D["RTPS (SPDP/SEDP)"]
  UDP_U["UDP unicast (data)"] --> RTPS_Data["RTPS (DATA/HEARTBEAT/ACKNACK)"]
  RTPS_Data --> CDR["CDR-encoded messages"]
  CDR --> ROS2["ROS 2 messages<br/>(sensor_msgs, geometry_msgs, etc.)"]
```

| Port | Usage |
|------|-------|
| 7400 + offsets | Discovery (multicast and unicast, per domain/participant) |
| 7401 + offsets | User data (unicast) |

DDS implementations also support TCP and shared memory transports for scenarios where UDP multicast is unavailable.

## Standards

| Document | Title |
|----------|-------|
| [OMG DDS v1.4](https://www.omg.org/spec/DDS/) | Data Distribution Service for Real-Time Systems |
| [OMG DDSI-RTPS v2.5](https://www.omg.org/spec/DDSI-RTPS/) | DDS Interoperability Wire Protocol (RTPS) |
| [OMG DDS-XTypes v1.3](https://www.omg.org/spec/DDS-XTypes/) | Extensible and Dynamic Topic Types |
| [OMG DDS Security v1.1](https://www.omg.org/spec/DDS-SECURITY/) | DDS Security Specification |
| [ROS 2 Design](https://design.ros2.org/) | ROS 2 middleware abstraction design |

## See Also

- [UDP](../transport-layer/udp.md) — primary transport for RTPS
- [MQTT](../messaging/mqtt.md) — alternative IoT pub-sub (broker-based, simpler)
- [RTP](../voip/rtp.md) — real-time media transport (different domain)
