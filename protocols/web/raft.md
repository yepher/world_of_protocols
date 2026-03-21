# Raft Consensus Protocol

> **Standard:** [In Search of an Understandable Consensus Algorithm](https://raft.github.io/raft.pdf) (Ongaro & Ousterhout, 2014) | **Layer:** Application (Layer 7) | **Wireshark filter:** N/A (application-level, typically gRPC or custom TCP)

Raft is a consensus algorithm for managing a replicated log across a cluster of servers. It was designed as an understandable alternative to Paxos, decomposing consensus into three sub-problems: leader election, log replication, and safety. Raft guarantees that all nodes in a cluster agree on the same sequence of state machine commands, even in the presence of failures. It is the consensus engine behind etcd, Consul, CockroachDB, TiKV, and many other distributed systems.

## Node Roles

Every server in a Raft cluster is in one of three states at any time:

| Role | Description |
|------|-------------|
| Leader | Handles all client requests, replicates log entries to followers, sends heartbeats |
| Follower | Passive -- responds to RPCs from leader and candidates |
| Candidate | Transitional state during leader election; requests votes from peers |

```mermaid
graph LR
  Follower -->|election timeout| Candidate
  Candidate -->|receives majority votes| Leader
  Candidate -->|discovers higher term| Follower
  Leader -->|discovers higher term| Follower
  Candidate -->|election timeout, new election| Candidate
```

## RequestVote RPC

Used by candidates to gather votes during an election.

```mermaid
packet-beta
  0-31: "term (4 bytes)"
  32-63: "candidateId (4 bytes)"
  64-95: "lastLogIndex (4 bytes)"
  96-127: "lastLogTerm (4 bytes)"
```

### RequestVote Response

```mermaid
packet-beta
  0-31: "term (4 bytes)"
  32-63: "voteGranted (bool)"
```

## AppendEntries RPC

Used by the leader for log replication and as a heartbeat (with empty entries).

```mermaid
packet-beta
  0-31: "term (4 bytes)"
  32-63: "leaderId (4 bytes)"
  64-95: "prevLogIndex (4 bytes)"
  96-127: "prevLogTerm (4 bytes)"
  128-159: "entries[] (variable) ..."
  160-191: "leaderCommit (4 bytes)"
```

### AppendEntries Response

```mermaid
packet-beta
  0-31: "term (4 bytes)"
  32-63: "success (bool)"
```

## InstallSnapshot RPC

Used by the leader to send a snapshot to followers that are too far behind.

```mermaid
packet-beta
  0-31: "term (4 bytes)"
  32-63: "leaderId (4 bytes)"
  64-95: "lastIncludedIndex (4 bytes)"
  96-127: "lastIncludedTerm (4 bytes)"
  128-159: "offset (4 bytes)"
  160-191: "data[] (variable) ..."
  192-223: "done (bool)"
```

## Key Fields

| Field | RPC | Description |
|-------|-----|-------------|
| term | All | Monotonically increasing logical clock; identifies the election epoch |
| candidateId | RequestVote | ID of the candidate requesting the vote |
| lastLogIndex | RequestVote | Index of the candidate's last log entry |
| lastLogTerm | RequestVote | Term of the candidate's last log entry |
| voteGranted | RequestVote Response | True if the follower granted its vote |
| leaderId | AppendEntries | ID of the current leader (so followers can redirect clients) |
| prevLogIndex | AppendEntries | Index of log entry immediately preceding new ones |
| prevLogTerm | AppendEntries | Term of the prevLogIndex entry |
| entries[] | AppendEntries | Log entries to replicate (empty for heartbeat) |
| leaderCommit | AppendEntries | Leader's commit index |
| success | AppendEntries Response | True if follower's log matched prevLogIndex/prevLogTerm |

## Leader Election

```mermaid
sequenceDiagram
  participant S1 as Server 1 (Follower)
  participant S2 as Server 2 (Follower)
  participant S3 as Server 3 (Follower)

  Note over S1,S3: Leader (old) crashes, election timeouts expire
  Note over S2: Election timeout fires first (randomized 150-300ms)
  S2->>S2: Increments term to T+1, votes for self, becomes Candidate
  S2->>S1: RequestVote (term=T+1, lastLogIndex=5, lastLogTerm=T)
  S2->>S3: RequestVote (term=T+1, lastLogIndex=5, lastLogTerm=T)
  S1->>S2: RequestVote Response (term=T+1, voteGranted=true)
  S3->>S2: RequestVote Response (term=T+1, voteGranted=true)
  Note over S2: Received majority (3/3) -- becomes Leader
  S2->>S1: AppendEntries (heartbeat, entries=[])
  S2->>S3: AppendEntries (heartbeat, entries=[])
```

Election rules:
- Each server votes for at most one candidate per term (first-come-first-served)
- Candidate must have a log at least as up-to-date as the voter's
- Randomized election timeouts (typically 150-300ms) prevent split votes
- A candidate that receives a majority of votes becomes leader

## Log Replication

```mermaid
sequenceDiagram
  participant C as Client
  participant L as Leader
  participant F1 as Follower 1
  participant F2 as Follower 2

  C->>L: Command (e.g., SET x=5)
  L->>L: Append entry to local log (index=6, term=3)
  L->>F1: AppendEntries (prevLogIndex=5, entries=[{index=6, term=3, cmd=SET x=5}])
  L->>F2: AppendEntries (prevLogIndex=5, entries=[{index=6, term=3, cmd=SET x=5}])
  F1->>L: AppendEntries Response (success=true)
  F2->>L: AppendEntries Response (success=true)
  Note over L: Majority confirmed -- commit index advances to 6
  L->>L: Apply SET x=5 to state machine
  L->>C: Response (OK)
  Note over L: Next heartbeat carries updated leaderCommit=6
  L->>F1: AppendEntries (leaderCommit=6)
  L->>F2: AppendEntries (leaderCommit=6)
  Note over F1,F2: Followers apply committed entries to their state machines
```

Replication rules:
- Leader appends the command to its local log
- Leader sends AppendEntries to all followers in parallel
- Entry is committed once a majority of servers have written it
- Committed entries are applied to the state machine in log order
- If a follower's log is inconsistent, the leader decrements nextIndex and retries

## Leader Failure and Recovery

```mermaid
sequenceDiagram
  participant C as Client
  participant L1 as Leader (Server 1)
  participant F2 as Follower (Server 2)
  participant F3 as Follower (Server 3)

  C->>L1: Command
  L1->>F2: AppendEntries
  L1->>F3: AppendEntries
  Note over L1: CRASHES
  Note over F2,F3: Election timeout expires
  F3->>F3: Becomes Candidate (term+1)
  F3->>F2: RequestVote
  F2->>F3: voteGranted=true
  Note over F3: Becomes new Leader
  F3->>F2: AppendEntries (heartbeat)
  C->>F3: Retries command (redirected or discovered new leader)
  Note over L1: Server 1 recovers as Follower
  F3->>L1: AppendEntries (brings log up to date)
```

## Safety Properties

| Property | Guarantee |
|----------|-----------|
| Election Safety | At most one leader per term |
| Leader Append-Only | Leader never overwrites or deletes log entries; it only appends |
| Log Matching | If two logs contain an entry with the same index and term, all preceding entries are identical |
| Leader Completeness | If an entry is committed in a given term, it will be present in the logs of all leaders for higher terms |
| State Machine Safety | If a server applies a log entry at a given index, no other server applies a different entry at that index |

## Membership Changes

Raft supports dynamic cluster membership changes without downtime:

| Approach | Description |
|----------|-------------|
| Single-server changes | Add or remove one server at a time; safe because any majority of the old and new configurations overlap |
| Joint consensus | Two-phase approach for arbitrary changes; the cluster transitions through a joint configuration |

## Log Compaction

As the log grows, Raft uses snapshots to compact it:

| Concept | Description |
|---------|-------------|
| Snapshot | Captures the entire state machine state at a given log index |
| lastIncludedIndex | The last log entry included in the snapshot |
| lastIncludedTerm | The term of that entry |
| InstallSnapshot RPC | Leader sends snapshot to slow followers instead of replaying the entire log |

## Raft vs Paxos

| Feature | Raft | Paxos |
|---------|------|-------|
| Design goal | Understandability | Theoretical elegance |
| Leader | Strong leader required | Optional (Multi-Paxos uses leader) |
| Election | Randomized timeouts, single round | Complex, multi-round possible |
| Log replication | Leader-driven, sequential | Proposer-driven, out-of-order possible |
| Membership changes | Built-in (joint consensus or single-server) | Not specified in basic Paxos |
| Implementations | etcd, Consul, CockroachDB, TiKV | Chubby, Spanner (modified) |
| Specification | Single paper, clear rules | Multiple papers, many variants |
| Understandability | High (designed for clarity) | Low (notoriously difficult) |

## Encapsulation

```mermaid
graph LR
  gRPC["gRPC / TCP"] --> Raft["Raft RPCs"]
  Raft --> StateMachine["Replicated State Machine"]
```

Raft RPCs are typically carried over gRPC (etcd, TiKV) or custom TCP protocols. The wire format varies by implementation since Raft defines the algorithm, not a wire protocol.

## Standards

| Document | Title |
|----------|-------|
| [Raft Paper](https://raft.github.io/raft.pdf) | In Search of an Understandable Consensus Algorithm (Ongaro & Ousterhout, 2014) |
| [Raft Dissertation](https://web.stanford.edu/~ouster/cgi-bin/papers/OngaroPhD.pdf) | Consensus: Bridging Theory and Practice (Ongaro, 2014) |
| [raft.github.io](https://raft.github.io/) | Raft Consensus Algorithm — resources and implementations |

## See Also

- [gRPC](grpc.md) -- common transport for Raft implementations (etcd, TiKV)
- [HTTP](http.md) -- client-facing API for Raft-backed services
