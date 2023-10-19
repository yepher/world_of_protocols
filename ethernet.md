## Ethernet

Ethernet is a widely-used local area network (LAN) technology that enables devices to communicate over a wired connection using a standardized protocol. It was developed by Robert Metcalfe and David Boggs at Xerox PARC in the 1970s.

It uses a bus topology and CSMA/CD access method. The terms Ethernet and the [IEEE 802.3](https://en.wikipedia.org/wiki/IEEE_802.3) standard are often used interchangeably.

### Ethernet Frame

An Ethernet frame is the basic unit of data transmission in Ethernet. It contains various fields that hold information about the source, destination, type, and actual data being transmitted. Here's a breakdown of a standard Ethernet frame:

```
+-------------------+-------------------+-------------------+-------------------+-------------------+------------------+
| Destination MAC   | Source MAC        | Type/Length       | Data and Padding  | Frame Check       |
| (6 bytes)         | (6 bytes)         | (2 bytes)         | (46-1500 bytes)   | Sequence (4 bytes)|
+-------------------+-------------------+-------------------+-------------------+-------------------+------------------+
```

#### Fields:

1. **Destination MAC:** The MAC address of the receiving device.
2. **Source MAC:** The MAC address of the sending device.
3. **Type/Length:** Specifies either the type of protocol or the length of the data.
4. **Data and Padding:** LLC protocol; Contains the actual data being sent. The size can vary, and padding is used to ensure a minimum frame size.
5. **Frame Check Sequence:** A 4-byte value used for error-checking to ensure the integrity of the data.


**Destination Address**

```
+-----+-----+--------------+
| I/G | U/L | Address bits |
+-----+-----+--------------+
```

* I/G Individual/Group address may be:
	* 0 Individual
	* 1 Group Address
* U/L Universal/local address may be:
	* 0 Universally administered
	* 1 Locally administered


**Source Address**

```
+---+-----+--------------+
| 0 | U/L | Address bits |
+---+-----+--------------+
```

* 0 first bit is always 0
* U/L Universal/local address may be:
	* 0 Universally administered
	* 1 Locally administered


**Length/type**

In the Ethernet protocol, the value (`≥0x0600` HEX) of this field is Ethernet Type, indicating the protocol inside

In the 802.3 protocol, the value (`46-1500` DEC) is the length of the inner protocol, which is the LLC encapsulated inner protocol. (The LLC header indicates the inner protocol type.)

It is prevalent to see this set to [IP](ip.md) `0x8000`.


### Ethernet Standards

There are several Ethernet standards, defined by the IEEE 802.3 committee. These standards dictate various aspects like speed, transmission method, and physical medium. Some popular standards include:

- **10Base-T:** 10 Mbps over twisted pair cables.
- **100Base-TX (Fast Ethernet):** 100 Mbps over twisted pair cables.
- **1000Base-T (Gigabit Ethernet):** 1 Gbps over twisted pair cables.
- **10GBase-T:** 10 Gbps over twisted pair cables.

Ethernet has continued to evolve with faster speeds and newer standards like 25G, 40G, and 100G Ethernet.

### Conclusion

Ethernet has been foundational in the realm of networking, providing a robust and standardized method for devices to communicate. Its frame structure ensures efficient and reliable data transmission, while continuous evolution in standards caters to increasing data demands.
