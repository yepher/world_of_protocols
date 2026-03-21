# OBD-II (On-Board Diagnostics II)

> **Standard:** [SAE J1979](https://www.sae.org/standards/content/j1979_202202/) / [ISO 15031](https://www.iso.org/standard/66369.html) | **Layer:** Application (over CAN / K-Line / J1850) | **Wireshark filter:** `iso15765`

OBD-II is a mandatory diagnostic interface for all passenger vehicles sold in the US (since 1996) and Europe (EOBD, since 2001). It provides standardized access to engine parameters, emissions data, and diagnostic trouble codes (DTCs) through a 16-pin connector under the dashboard. The most common physical layer is CAN (ISO 15765), though older vehicles may use K-Line (ISO 14230) or J1850 (legacy US). OBD-II defines a request-response protocol where a diagnostic tool sends a Service ID (mode) + Parameter ID (PID), and the ECU responds with the requested data.

## Physical Layers

| Protocol | Standard | Speed | Notes |
|----------|----------|-------|-------|
| CAN (most common) | ISO 15765-4 | 250 / 500 kbps | Standard since ~2008, required in US since 2008 |
| K-Line | ISO 14230 (KWP2000) | 10.4 kbps | Single-wire bidirectional, older European vehicles |
| J1850 VPW | SAE J1850 | 10.4 kbps | Variable Pulse Width, legacy GM |
| J1850 PWM | SAE J1850 | 41.6 kbps | Pulse Width Modulation, legacy Ford |
| ISO 9141-2 | ISO 9141 | 10.4 kbps | K-Line variant, older Asian/European |

## DLC (Data Link Connector) — SAE J1962

```mermaid
packet-beta
  0-7: "Pin 1: Vendor"
  8-15: "Pin 2: J1850 Bus+"
  16-23: "Pin 3: Vendor"
  24-31: "Pin 4: Chassis GND"
  32-39: "Pin 5: Signal GND"
  40-47: "Pin 6: CAN-H (ISO 15765)"
  48-55: "Pin 7: K-Line (ISO 9141)"
  56-63: "Pin 8: Vendor"
```

```mermaid
packet-beta
  0-7: "Pin 9: Vendor"
  8-15: "Pin 10: J1850 Bus-"
  16-23: "Pin 11: Vendor"
  24-31: "Pin 12: Vendor"
  32-39: "Pin 13: Vendor"
  40-47: "Pin 14: CAN-L (ISO 15765)"
  48-55: "Pin 15: L-Line (ISO 9141)"
  56-63: "Pin 16: Battery +12V"
```

Key pins: **6** (CAN-H), **14** (CAN-L), **4/5** (ground), **16** (+12V power), **7** (K-Line).

## CAN-Based OBD Request/Response IDs

| CAN ID | Direction | Description |
|--------|-----------|-------------|
| 0x7DF | Request (functional) | Broadcast to all ECUs ("anyone who supports this PID") |
| 0x7E0-0x7E7 | Request (physical) | Addressed to specific ECU (0x7E0 = engine ECU) |
| 0x7E8-0x7EF | Response | Response from ECU (0x7E8 = engine ECU response) |

## CAN OBD Frame (ISO 15765 — Single Frame)

```mermaid
packet-beta
  0-10: "CAN ID (11 bits, e.g. 0x7DF)"
  11-14: "DLC (=8)"
  15-18: "PCI: Len"
  19-26: "Service ID (Mode)"
  27-34: "PID"
  35-58: "Data (0-4 bytes)"
  59-82: "Padding (0x55 or 0x00)"
```

For CAN-based OBD, each request/response is wrapped in ISO-TP (ISO 15765-2) framing. Most PID responses fit in a single CAN frame.

### ISO-TP Frame Types (ISO 15765-2)

| PCI Type | Nibble | Description |
|----------|--------|-------------|
| Single Frame (SF) | 0x0 | Complete message in one frame, lower nibble = length |
| First Frame (FF) | 0x1 | First of multi-frame, followed by length (12 bits) |
| Consecutive Frame (CF) | 0x2 | Continuation, lower nibble = sequence number (0-F) |
| Flow Control (FC) | 0x3 | Receiver controls sender's pacing (BS, STmin) |

## Service IDs (Modes)

| Service (hex) | Name | Description |
|---------------|------|-------------|
| 0x01 | Current Data | Read real-time sensor values (PIDs) |
| 0x02 | Freeze Frame | Snapshot of data when DTC was set |
| 0x03 | Read DTCs | Retrieve confirmed diagnostic trouble codes |
| 0x04 | Clear DTCs | Clear DTCs and reset MIL (check engine light) |
| 0x05 | O2 Sensor Monitoring | Oxygen sensor test results |
| 0x06 | On-Board Test Results | Non-continuous monitoring test results |
| 0x07 | Pending DTCs | DTCs detected during current drive cycle |
| 0x08 | Control On-Board System | Actuator tests (manufacturer-specific) |
| 0x09 | Vehicle Information | VIN, calibration IDs, ECU name |
| 0x0A | Permanent DTCs | DTCs that persist even after clearing |

## Common PIDs (Service 0x01)

| PID (hex) | Name | Formula | Unit |
|-----------|------|---------|------|
| 0x00 | Supported PIDs [01-20] | Bit-encoded (each bit = one PID supported) | bitmask |
| 0x04 | Calculated Engine Load | A / 2.55 | % |
| 0x05 | Engine Coolant Temp | A - 40 | C |
| 0x0C | Engine RPM | (256*A + B) / 4 | rpm |
| 0x0D | Vehicle Speed | A | km/h |
| 0x0F | Intake Air Temp | A - 40 | C |
| 0x10 | MAF Air Flow Rate | (256*A + B) / 100 | g/s |
| 0x11 | Throttle Position | A / 2.55 | % |
| 0x1F | Run Time Since Start | 256*A + B | sec |
| 0x2F | Fuel Tank Level | A / 2.55 | % |
| 0x31 | Distance Since Codes Cleared | 256*A + B | km |

A, B = response data bytes.

## PID Request/Response

```mermaid
sequenceDiagram
  participant Tool as Scan Tool (Tester)
  participant ECU as Engine ECU

  Note over Tool: Read engine RPM
  Tool->>ECU: CAN ID 0x7DF: [02 01 0C 00 00 00 00 00]
  Note over Tool: Len=2, Service=01, PID=0C
  ECU->>Tool: CAN ID 0x7E8: [04 41 0C 1A F8 00 00 00]
  Note over ECU: Len=4, Service+0x40=41, PID=0C, A=0x1A, B=0xF8
  Note over Tool: RPM = (256*0x1A + 0xF8) / 4 = 1726 rpm
```

```mermaid
sequenceDiagram
  participant Tool as Scan Tool
  participant ECU as Engine ECU

  Note over Tool: Read vehicle speed
  Tool->>ECU: CAN ID 0x7DF: [02 01 0D 00 00 00 00 00]
  Note over Tool: Len=2, Service=01, PID=0D
  ECU->>Tool: CAN ID 0x7E8: [03 41 0D 3C 00 00 00 00]
  Note over ECU: Len=3, Service+0x40=41, PID=0D, A=0x3C
  Note over Tool: Speed = 0x3C = 60 km/h
```

## DTC Read / Clear

```mermaid
sequenceDiagram
  participant Tool as Scan Tool
  participant ECU as Engine ECU

  Note over Tool: Read confirmed DTCs (Service 03)
  Tool->>ECU: CAN ID 0x7DF: [01 03 00 00 00 00 00 00]
  ECU->>Tool: CAN ID 0x7E8: [06 43 02 01 43 01 96 00]
  Note over ECU: Service+0x40=43, DTC count=2<br/>DTC1=0x0143 (P0143), DTC2=0x0196 (P0196)
  Note over Tool: P0143 = O2 Sensor Low Voltage (B1S3)<br/>P0196 = Engine Oil Temp Sensor Range

  Note over Tool: Clear all DTCs (Service 04)
  Tool->>ECU: CAN ID 0x7DF: [01 04 00 00 00 00 00 00]
  ECU->>Tool: CAN ID 0x7E8: [01 44 00 00 00 00 00 00]
  Note over ECU: DTCs cleared, MIL off
```

## DTC Format

DTCs are 2 bytes (16 bits) encoded as follows:

| Bits | Field | Values |
|------|-------|--------|
| 15-14 | Category | 00=P (Powertrain), 01=C (Chassis), 10=B (Body), 11=U (Network) |
| 13-12 | Sub-type | 0=SAE standard, 1=Manufacturer-specific |
| 11-8 | System group | 0-F |
| 7-0 | Fault number | 00-FF |

### DTC Category Prefixes

| Prefix | System | Examples |
|--------|--------|----------|
| P0xxx | Powertrain (SAE-defined) | P0300 = Random misfire, P0420 = Catalyst efficiency |
| P1xxx | Powertrain (manufacturer) | Manufacturer-specific codes |
| C0xxx | Chassis | ABS, stability control, steering |
| B0xxx | Body | Airbags, HVAC, lighting |
| U0xxx | Network | CAN bus communication faults |

## VIN Read (Service 09, PID 02)

The Vehicle Identification Number requires multi-frame ISO-TP because it is 17 characters (> 8 bytes):

```mermaid
sequenceDiagram
  participant Tool as Scan Tool
  participant ECU as Engine ECU

  Tool->>ECU: [02 09 02 ...] (Request VIN)
  ECU->>Tool: First Frame: [10 14 49 02 01 ...] (20 bytes total, VIN chars 1-3)
  Tool->>ECU: Flow Control: [30 00 00 ...] (clear to send)
  ECU->>Tool: Consecutive Frame: [21 ...] (VIN chars 4-10)
  ECU->>Tool: Consecutive Frame: [22 ...] (VIN chars 11-17)
  Note over Tool: VIN = "1HGBH41JXMN109186" (17 ASCII chars)
```

## Encapsulation (CAN-Based OBD)

```mermaid
graph LR
  CAN["CAN 2.0A (ISO 11898)"] --> ISOTP["ISO-TP (ISO 15765-2)"] --> OBD["OBD-II (SAE J1979)"]
```

## Standards

| Document | Title |
|----------|-------|
| [SAE J1979](https://www.sae.org/standards/content/j1979_202202/) | OBD-II diagnostic services (modes/PIDs) |
| [SAE J1962](https://www.sae.org/standards/content/j1962_201607/) | OBD-II diagnostic connector (DLC) |
| [ISO 15765-4](https://www.iso.org/standard/66570.html) | OBD on CAN (emissions-related) |
| [ISO 15765-2](https://www.iso.org/standard/66574.html) | ISO-TP transport protocol for CAN |
| [ISO 15031-5](https://www.iso.org/standard/66369.html) | Emissions-related diagnostic services |
| [ISO 15031-6](https://www.iso.org/standard/66370.html) | DTC definitions |
| [ISO 14230](https://www.iso.org/standard/54310.html) | KWP2000 (K-Line diagnostics) |
| [SAE J1850](https://www.sae.org/standards/content/j1850_201510/) | J1850 VPW/PWM physical layer |

## See Also

- [CAN](../bus/can.md) -- physical and data link layer for modern OBD-II
- [J1939](j1939.md) -- heavy-duty vehicle protocol (also CAN-based)
- [DoIP / UDS](doip.md) -- modern Ethernet-based diagnostics replacing OBD-II in newer vehicles
- [SOME/IP](someip.md) -- automotive Ethernet middleware
