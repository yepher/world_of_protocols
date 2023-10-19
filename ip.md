## IP (Internet Protocol)

See also [IPv6](ipv6.md)

IP is the principal communications protocol for relaying datagrams (packets) across network boundaries. It facilitates the logical addressing and routing of packets in a network, allowing data to be transmitted between devices with unique IP addresses. IP is the primary protocol in the Internet Layer of the Internet Protocol Suite and is used in conjunction with the Transport Layer protocols, such as TCP and UDP.

IP is most commonly used by the TCP/IP and UDP/IP suites. 

### IP Packet Structure

An IP packet is the fundamental unit for data transmission in IP-based networks. It consists of a header and payload. Here's the basic structure of an IP packet:

```
      4     8                16                         32 bits
+-----+-----+-----------------+-------------------------+
| Ver | IHL | Type of service | Total length            |
------------------------------+-------+-----------------+
| Identification              | Flags | Fragment offset |
+-----------------------------+-------------------------+
|Time to live | Protocol      | Header Checksum         |
+-------------------------------------------------------+
|                    Source Address                     |
+-------------------------------------------------------+
|                   Destination Address                 |
+-------------------------------------------------------+
|                    Option + Padding                   |
+-------------------------------------------------------+
|                          Data                         |
+-------------------------------------------------------+
```



#### IP Header Fields:

1. **Version (4 bits):** Specifies the version of the Internet Protocol. Typical values are 4 (IPv4) and 6 (IPv6).
2. **Internet Header Length (4 bits):** Indicates the header's length in 32-bit words. Points to the beginning of the data. The minimum value for a correct header is 5.
3. **Type of Service/DS Field (8 bits, IPv4):** Used for Quality of Service (QoS) configuration.
4. **Total Length (16 bits, IPv4 only):** Specifies the entire packet size, including header and data.
5. **Identification (16 bits, IPv4 only):** Unique identifier for each datagram.
6. **Flags and Fragment Offset (13 bits, IPv4 only):** Used for fragmentation and reassembly.
7. **Time to Live (8 bits, IPv4) / Hop Limit (8 bits, IPv6):** Limits the lifespan of the datagram.
8. **Protocol (8 bits, IPv4 only):** Identifies the next level protocol (e.g., TCP, UDP).
9. **Header Checksum (16 bits, IPv4 only):** Used for error-checking of the header.
10. **Source IP Address:** Originating IP address of the datagram.
11. **Destination IP Address:** Destination IP address for the datagram.
12. **Options (IPv4 only):** Additional header fields; not always present.

**Type of Service**

Indicates the quality of service desigred.

* Bits 0-2: Precedences
	* 111 Network control
	* 110 Internetwork control
	* 101 CRITIC/ECP
	* 100 Flash override
	* 011 Flash
	* 010 Immediate
	* 001 Priority
	* 000 Routine
* Bit 3: Delay
	* 0 Normal delay
	* 1 Low delay
* Bit 4: Throughput
	* 0 Normal throughput
	* 1 High throughput
* Bit 5: Reliability
	* 0 Normal reliability
	* 1 High reliability
* Bits 6-7: Reserved for future use

**Flags**

3 bits. Control Flags:

* Bit 0: reserved and must be zero
* Bit 1: Don't fragment bit
	* 0 May fragment
	* 1. Don't fragment
* Bit 2: More fragments bit
	* 0 Last fragment
	* 1 More fragments

### IP Addressing

Every device on an IP network is identified by a unique IP address. There are two versions of IP addressing:

- **IPv4:** Uses 32-bit addresses, often represented in dotted-decimal notation (e.g., 192.168.1.1).
- **IPv6:** Uses 128-bit addresses, represented in hexadecimal notation (e.g., 2001:0db8:85a3:0000:0000:8a2e:0370:7334).

### IP's Role in the Internet Protocol Suite

IP operates at the third layer of the OSI model, the Network Layer, and at the Internet layer in the Internet Protocol Suite. Its role is to deliver packets based on the IP addresses in the packet headers. It uses routing protocols, such as BGP and OSPF, to determine the best path for each packet.

### Conclusion

IP is the backbone protocol of the internet, enabling devices to communicate across diverse networks. With its robust addressing and routing mechanisms, IP ensures that data is efficiently and accurately delivered across the globe.

