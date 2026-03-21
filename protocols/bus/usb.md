# USB (Universal Serial Bus)

> **Standard:** [USB Specification (usb.org)](https://www.usb.org/documents) | **Layer:** Full stack (Physical through Application) | **Wireshark filter:** `usb`

USB is the dominant wired peripheral interconnect, connecting keyboards, mice, storage, cameras, phones, audio devices, and virtually every computer peripheral manufactured since the late 1990s. It uses a host-controlled, polled bus architecture where the host initiates all data transfers. USB has evolved through multiple generations — from 1.5 Mbps (USB 1.0 Low Speed) to 120 Gbps (USB4). USB Power Delivery enables up to 240W charging over the same cable.

## Protocol Stack

```mermaid
graph TD
  Class["Device Class Drivers<br/>(HID, Mass Storage, Audio, CDC, Video)"]
  Function["Function Layer<br/>(Endpoints, Interfaces)"]
  Device["Device Layer<br/>(Device, Configuration, Interface descriptors)"]
  Pipe["Pipe Layer<br/>(Control, Bulk, Interrupt, Isochronous)"]
  Transaction["Transaction Layer<br/>(Token, Data, Handshake packets)"]
  Packet["Packet Layer<br/>(PID, Address, Endpoint, CRC)"]
  PHY["Physical Layer<br/>(Signaling, Connectors)"]

  Class --> Function --> Device --> Pipe --> Transaction --> Packet --> PHY
```

## Token Packet (USB 2.0)

```mermaid
packet-beta
  0-7: "PID (8 bits)"
  8-14: "Address (7 bits)"
  15-18: "Endpoint (4 bits)"
  19-23: "CRC5"
```

## Data Packet

```mermaid
packet-beta
  0-7: "PID (8 bits)"
  8-15: "Data (0-1024 bytes) ..."
  16-31: "CRC16"
```

## Packet IDs (PIDs)

| Category | PID | Name | Description |
|----------|-----|------|-------------|
| Token | 0x01 | OUT | Host to device transfer |
| Token | 0x09 | IN | Device to host transfer |
| Token | 0x05 | SOF | Start of Frame (1 ms marker) |
| Token | 0x0D | SETUP | Control transfer setup stage |
| Data | 0x03 | DATA0 | Data packet (even) |
| Data | 0x0B | DATA1 | Data packet (odd — for toggle) |
| Data | 0x07 | DATA2 | High-speed isochronous |
| Data | 0x0F | MDATA | High-speed split |
| Handshake | 0x02 | ACK | Transfer accepted |
| Handshake | 0x0A | NAK | Device busy, retry later |
| Handshake | 0x0E | STALL | Error — endpoint halted |
| Handshake | 0x06 | NYET | Not yet (high-speed flow control) |

## Transfer Types

| Type | Use Case | Max Size (HS) | Guaranteed Bandwidth | Error Recovery |
|------|----------|---------------|---------------------|----------------|
| Control | Device setup, configuration | 64 bytes | No | Yes (retry) |
| Bulk | Large data (storage, printing) | 512 bytes | No | Yes (retry) |
| Interrupt | Periodic input (keyboard, mouse) | 1024 bytes | Yes (polling interval) | Yes (retry) |
| Isochronous | Streaming (audio, video) | 1024 bytes | Yes (reserved) | No (no retry) |

### Control Transfer

```mermaid
sequenceDiagram
  participant H as Host
  participant D as Device

  H->>D: SETUP token + DATA0 (8-byte setup packet)
  D->>H: ACK

  Note over H,D: Data Stage (optional)
  H->>D: IN token
  D->>H: DATA1 (response data)
  H->>D: ACK

  Note over H,D: Status Stage
  H->>D: OUT token + zero-length DATA1
  D->>H: ACK
```

## Setup Packet (Control Transfers)

```mermaid
packet-beta
  0-7: "bmRequestType"
  8-15: "bRequest"
  16-31: "wValue"
  32-47: "wIndex"
  48-63: "wLength"
```

### Standard Requests

| bRequest | Name | Description |
|----------|------|-------------|
| 0 | GET_STATUS | Read device/endpoint status |
| 1 | CLEAR_FEATURE | Clear a feature (e.g., endpoint halt) |
| 5 | SET_ADDRESS | Assign a device address (1-127) |
| 6 | GET_DESCRIPTOR | Read device, configuration, or string descriptor |
| 9 | SET_CONFIGURATION | Activate a device configuration |
| 11 | SET_INTERFACE | Select an alternate interface setting |

## Descriptor Hierarchy

```mermaid
graph TD
  DD["Device Descriptor"]
  DD --> CD1["Configuration 1"]
  CD1 --> IF1["Interface 0<br/>(e.g., HID Keyboard)"]
  CD1 --> IF2["Interface 1<br/>(e.g., HID Mouse)"]
  IF1 --> EP1["Endpoint 1 IN<br/>(Interrupt)"]
  IF2 --> EP2["Endpoint 2 IN<br/>(Interrupt)"]
```

## Common Device Classes

| Class | Code | Description | Examples |
|-------|------|-------------|----------|
| HID | 0x03 | Human Interface Device | Keyboard, mouse, gamepad |
| Mass Storage | 0x08 | Block storage (SCSI over USB) | Flash drives, external HDDs |
| CDC | 0x02 | Communications Device | USB serial (ACM), Ethernet (ECM/NCM) |
| Audio | 0x01 | Audio streaming and control | USB microphones, DACs, headsets |
| Video | 0x0E | Video streaming (UVC) | Webcams |
| Printer | 0x07 | Printing | USB printers |
| Wireless | 0xE0 | Wireless controllers | Bluetooth adapters |
| Vendor Specific | 0xFF | Custom protocols | Proprietary devices |

## USB Generations

| Version | Year | Speed | Marketing Name | Connector |
|---------|------|-------|---------------|-----------|
| 1.0 | 1996 | 1.5 Mbps (Low) / 12 Mbps (Full) | USB | A, B |
| 2.0 | 2000 | 480 Mbps | Hi-Speed | A, B, Mini, Micro |
| 3.0 | 2008 | 5 Gbps | SuperSpeed | A, B, Micro-B (blue) |
| 3.1 | 2013 | 10 Gbps | SuperSpeed+ | A, C |
| 3.2 | 2017 | 20 Gbps | SuperSpeed 20Gbps | C |
| USB4 | 2019 | 40 Gbps | USB4 40Gbps | C |
| USB4 v2 | 2022 | 120 Gbps | USB4 120Gbps | C |

## USB Type-C

| Feature | Description |
|---------|-------------|
| Connector | Reversible, 24-pin |
| USB PD | Up to 240W (48V × 5A) power delivery |
| Alternate Modes | DisplayPort, Thunderbolt, HDMI over USB-C |
| USB4 | Tunnels USB 3.x, DisplayPort, and PCIe over USB-C |

## Standards

| Document | Title |
|----------|-------|
| [USB 2.0 Spec](https://www.usb.org/document-library/usb-20-specification) | USB 2.0 Specification |
| [USB 3.2 Spec](https://www.usb.org/document-library/usb-32-specification) | USB 3.2 Specification |
| [USB4 Spec](https://www.usb.org/document-library/usb4-specification) | USB4 Specification |
| [USB PD Spec](https://www.usb.org/document-library/usb-power-delivery) | USB Power Delivery Specification |
| [USB Type-C Spec](https://www.usb.org/document-library/usb-type-cr-cable-and-connector-specification) | USB Type-C Cable and Connector Specification |

## See Also

- [I2C](i2c.md) — low-speed IC bus (some USB devices bridge to I2C)
- [SPI](spi.md) — IC bus (some USB devices bridge to SPI)
- [Bluetooth](../wireless/bluetooth.md) — wireless alternative for peripherals
