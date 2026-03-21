# Kafka Protocol

> **Standard:** [Apache Kafka Protocol Guide](https://kafka.apache.org/protocol) | **Layer:** Application (Layer 7) | **Wireshark filter:** `kafka`

The Kafka protocol is a binary, request-response protocol for interacting with Apache Kafka brokers. Kafka is a distributed event streaming platform used for log aggregation, event sourcing, stream processing, and as a durable message bus between microservices. Clients produce records to topics (partitioned, replicated logs) and consumers read them by tracking offsets. The protocol defines how producers, consumers, and admin tools communicate with the broker cluster.

## Request/Response Frame

Every Kafka message uses a length-prefixed binary format:

```mermaid
packet-beta
  0-31: "Size (4 bytes)"
  32-47: "API Key"
  48-63: "API Version"
  64-95: "Correlation ID"
  96-127: "Client ID (string) ..."
  128-159: "Request Body ..."
```

### Response

```mermaid
packet-beta
  0-31: "Size (4 bytes)"
  32-63: "Correlation ID"
  64-95: "Response Body ..."
```

## Key Fields

| Field | Size | Description |
|-------|------|-------------|
| Size | 4 bytes | Length of the remaining message |
| API Key | 16 bits | Identifies the request type |
| API Version | 16 bits | Version of the API being used |
| Correlation ID | 32 bits | Client-assigned ID matching responses to requests |
| Client ID | Variable | Nullable string identifying the client |

## API Keys (Request Types)

| Key | Name | Description |
|-----|------|-------------|
| 0 | Produce | Write records to a topic partition |
| 1 | Fetch | Read records from a topic partition |
| 2 | ListOffsets | Get available offsets for a partition |
| 3 | Metadata | Get cluster and topic metadata |
| 8 | OffsetCommit | Commit consumer offsets |
| 9 | OffsetFetch | Fetch committed offsets |
| 10 | FindCoordinator | Find the group coordinator broker |
| 11 | JoinGroup | Join a consumer group |
| 14 | SyncGroup | Synchronize group assignments |
| 18 | ApiVersions | Query supported API versions |
| 19 | CreateTopics | Create new topics |
| 20 | DeleteTopics | Delete topics |
| 22 | InitProducerID | Initialize idempotent/transactional producer |
| 32 | DescribeConfigs | Query broker/topic configuration |
| 36 | SaslAuthenticate | SASL authentication exchange |
| 37 | CreatePartitions | Add partitions to topics |

## Core Concepts

| Concept | Description |
|---------|-------------|
| Topic | Named stream of records (like a database table) |
| Partition | Ordered, immutable log within a topic |
| Offset | Sequential position within a partition |
| Record | Key + value + timestamp + headers |
| Producer | Writes records to topic partitions |
| Consumer | Reads records by tracking offsets |
| Consumer Group | Set of consumers that share partitions (load balancing) |
| Broker | Kafka server that stores partitions and serves clients |
| Replication | Each partition has N replicas across brokers |
| Leader | One replica handles all reads/writes; others are followers |

### Produce/Consume Flow

```mermaid
sequenceDiagram
  participant P as Producer
  participant B as Broker (Leader)
  participant C as Consumer

  P->>B: Produce (topic=orders, partition=0, records=[...])
  B->>P: ProduceResponse (base_offset=1000)

  C->>B: Fetch (topic=orders, partition=0, offset=1000)
  B->>C: FetchResponse (records=[...], high_watermark=1005)
  C->>B: OffsetCommit (group=myapp, partition=0, offset=1005)
```

### Consumer Group Rebalancing

```mermaid
sequenceDiagram
  participant C1 as Consumer 1
  participant C2 as Consumer 2
  participant Coord as Group Coordinator

  C1->>Coord: JoinGroup (group=myapp)
  C2->>Coord: JoinGroup (group=myapp)
  Coord->>C1: JoinGroupResponse (leader=C1, members=[C1,C2])
  Coord->>C2: JoinGroupResponse (leader=C1)
  C1->>Coord: SyncGroup (assignments: C1→[p0,p1], C2→[p2,p3])
  Coord->>C1: SyncGroupResponse (your partitions: p0, p1)
  Coord->>C2: SyncGroupResponse (your partitions: p2, p3)
```

## Record Batch Format (v2)

```mermaid
packet-beta
  0-63: "Base Offset (8 bytes)"
  64-95: "Batch Length (4 bytes)"
  96-127: "Partition Leader Epoch"
  128-135: "Magic (2)"
  136-167: "CRC32-C"
  168-183: "Attributes"
  184-215: "Last Offset Delta"
  216-279: "Timestamps ..."
  280-311: "Producer ID + Epoch"
  312-343: "Base Sequence + Record Count"
  344-375: "Records ..."
```

### Record Attributes

| Bit | Description |
|-----|-------------|
| 0-2 | Compression: 0=none, 1=gzip, 2=snappy, 3=lz4, 4=zstd |
| 3 | Timestamp type: 0=create, 1=log-append |
| 4 | Is transactional |
| 5 | Is control batch |

## Encapsulation

```mermaid
graph LR
  TCP9092["TCP port 9092"] --> Kafka["Kafka protocol"]
  TLS9093["TLS port 9093"] --> Kafka_TLS["Kafka (encrypted)"]
```

## Standards

| Document | Title |
|----------|-------|
| [Kafka Protocol Guide](https://kafka.apache.org/protocol) | Apache Kafka Protocol Specification |
| [KIP Index](https://cwiki.apache.org/confluence/display/KAFKA/Kafka+Improvement+Proposals) | Kafka Improvement Proposals (protocol evolution) |

## See Also

- [AMQP](amqp.md) — enterprise message queuing (different model)
- [MQTT](mqtt.md) — lightweight IoT messaging
- [NATS](nats.md) — lightweight cloud-native messaging
- [TCP](../transport-layer/tcp.md)
