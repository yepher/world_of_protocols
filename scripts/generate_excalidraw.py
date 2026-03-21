#!/usr/bin/env python3
"""Generate an Excalidraw protocol map with clickable links to GitHub."""

import json
import random

GITHUB_BASE = "https://github.com/yepher/world_of_protocols/blob/main/protocols"

def make_rect(id, x, y, w, h, bg, stroke, label, font=16, link=None, opacity=100):
    el = {
        "type": "rectangle",
        "id": id,
        "x": x, "y": y,
        "width": w, "height": h,
        "backgroundColor": bg,
        "fillStyle": "solid",
        "strokeColor": stroke,
        "strokeWidth": 1,
        "roundness": {"type": 3},
        "opacity": opacity,
        "angle": 0,
        "roughness": 1,
        "seed": random.randint(1, 999999),
    }
    if link:
        el["link"] = {"type": "url", "url": link}
    # Label as bound text
    return el, {
        "type": "text",
        "id": f"{id}_t",
        "x": x + 4, "y": y + 4,
        "width": w - 8, "height": h - 8,
        "text": label,
        "fontSize": font,
        "fontFamily": 1,
        "textAlign": "center",
        "verticalAlign": "middle",
        "strokeColor": "#1e1e1e",
        "containerId": id,
        "angle": 0,
        "roughness": 1,
        "seed": random.randint(1, 999999),
    }

def make_text(id, x, y, text, font=18, color="#1e1e1e"):
    return {
        "type": "text",
        "id": id,
        "x": x, "y": y,
        "width": len(text) * font * 0.6,
        "height": font + 4,
        "text": text,
        "fontSize": font,
        "fontFamily": 1,
        "textAlign": "left",
        "verticalAlign": "top",
        "strokeColor": color,
        "angle": 0,
        "roughness": 1,
        "seed": random.randint(1, 999999),
    }

def make_band(id, x, y, w, h, bg, stroke, opacity=40):
    return {
        "type": "rectangle",
        "id": id,
        "x": x, "y": y,
        "width": w, "height": h,
        "backgroundColor": bg,
        "fillStyle": "solid",
        "strokeColor": stroke,
        "strokeWidth": 1,
        "opacity": opacity,
        "angle": 0,
        "roughness": 1,
        "seed": random.randint(1, 999999),
    }

def make_arrow(id, x, y, dx, dy, color="#757575"):
    return {
        "type": "arrow",
        "id": id,
        "x": x, "y": y,
        "width": dx, "height": dy,
        "points": [[0, 0], [dx, dy]],
        "strokeColor": color,
        "strokeWidth": 1,
        "endArrowhead": "arrow",
        "startArrowhead": None,
        "angle": 0,
        "roughness": 1,
        "seed": random.randint(1, 999999),
    }

def gh(path):
    return f"{GITHUB_BASE}/{path}"

elements = []

# --- LAYER BANDS ---
BAND_W = 2300
elements.append(make_band("bg7", 0, 50, BAND_W, 170, "#dbe4ff", "#4a9eed", 40))
elements.append(make_band("bg6", 0, 230, BAND_W, 90, "#e5dbff", "#8b5cf6", 35))
elements.append(make_band("bg4", 0, 330, BAND_W, 100, "#d3f9d8", "#22c55e", 35))
elements.append(make_band("bg3", 0, 440, BAND_W, 140, "#fff3bf", "#f59e0b", 35))
elements.append(make_band("bg2", 0, 590, BAND_W, 140, "#ffd8a8", "#f59e0b", 35))
elements.append(make_band("bg1", 0, 740, BAND_W, 120, "#ffc9c9", "#ef4444", 30))

# --- TITLE ---
elements.append(make_text("title", 600, -50, "The World of Protocols", 36, "#1e1e1e"))
elements.append(make_text("subtitle", 580, -5, "github.com/yepher/world_of_protocols", 16, "#757575"))

# --- LAYER LABELS (left side) ---
elements.append(make_text("l7", 8, 55, "7  APPLICATION", 18, "#2563eb"))
elements.append(make_text("l6", 8, 235, "6  SECURITY", 18, "#7c3aed"))
elements.append(make_text("l4", 8, 335, "4  TRANSPORT", 18, "#15803d"))
elements.append(make_text("l3", 8, 445, "3  NETWORK", 18, "#b45309"))
elements.append(make_text("l2", 8, 595, "2  DATA LINK", 18, "#c2410c"))
elements.append(make_text("l1", 8, 745, "1  PHYSICAL", 18, "#dc2626"))

# --- COLUMN HEADERS ---
headers = [
    ("h_web", 210, "Web / API"),
    ("h_email", 470, "Email / Infra"),
    ("h_msg", 750, "Messaging"),
    ("h_voip", 980, "VoIP / Media"),
    ("h_vpn", 1250, "VPN / Tunnel"),
    ("h_tele", 1480, "Telecom"),
    ("h_iot", 1700, "IoT / Industrial"),
    ("h_wire", 1960, "Wireless"),
]
for hid, hx, htxt in headers:
    elements.append(make_text(hid, hx, 25, htxt, 16, "#555555"))

# --- COLORS ---
C_WEB = ("#a5d8ff", "#4a9eed")
C_INFRA = ("#c3fae8", "#06b6d4")
C_MSG = ("#b2f2bb", "#22c55e")
C_VOIP = ("#d0bfff", "#8b5cf6")
C_VPN = ("#ffc9c9", "#ef4444")
C_TELE = ("#eebefa", "#8b5cf6")
C_IOT = ("#ffd8a8", "#c2410c")
C_WIRE = ("#a5d8ff", "#4a9eed")
C_L2 = ("#ffd8a8", "#c2410c")
C_L1 = ("#ffc9c9", "#dc2626")
C_SEC = ("#d0bfff", "#8b5cf6")
C_NAT = ("#eebefa", "#ec4899")
C_AUTH = ("#c3fae8", "#06b6d4")

BW = 105  # box width
BH = 33   # box height
FS = 14   # font size

# ============================================================
# LAYER 7 - APPLICATION
# ============================================================

# Web / API column
protos_l7 = [
    # (id, x, y, label, colors, github_path)
    # Web
    ("http", 180, 60, "HTTP", C_WEB, "application-layer/http.md"),
    ("grpc", 180, 100, "gRPC", C_WEB, "application-layer/grpc.md"),
    ("ws", 290, 60, "WebSocket", C_WEB, "application-layer/websocket.md"),
    ("hls", 290, 100, "HLS/DASH", C_WEB, "application-layer/hls.md"),
    ("dns", 180, 140, "DNS", C_WEB, "application-layer/dns.md"),
    ("dhcp", 290, 140, "DHCP", C_WEB, "application-layer/dhcp.md"),
    ("dns2", 180, 180, "OTLP", C_WEB, "application-layer/otlp.md"),
    # Email / Infra
    ("smtp", 440, 60, "SMTP", C_INFRA, "application-layer/smtp.md"),
    ("imap", 550, 60, "IMAP", C_INFRA, "application-layer/imap.md"),
    ("pop3", 550, 100, "POP3", C_INFRA, "application-layer/pop3.md"),
    ("ldap", 440, 100, "LDAP", C_INFRA, "application-layer/ldap.md"),
    ("ssh", 440, 140, "SSH", C_INFRA, "application-layer/ssh.md"),
    ("ftp", 550, 140, "FTP", C_INFRA, "application-layer/ftp.md"),
    ("snmp", 660, 60, "SNMP", C_INFRA, "application-layer/snmp.md"),
    ("radius", 660, 100, "RADIUS", C_INFRA, "application-layer/radius.md"),
    ("ntp", 660, 140, "NTP", C_INFRA, "application-layer/ntp.md"),
    ("telnet", 660, 180, "Telnet", C_INFRA, "application-layer/telnet.md"),
    # Messaging
    ("mqtt", 770, 60, "MQTT", C_MSG, "application-layer/mqtt.md"),
    ("amqp", 770, 100, "AMQP", C_MSG, "application-layer/amqp.md"),
    ("nats", 770, 140, "NATS", C_MSG, "application-layer/nats.md"),
    ("kafka", 880, 60, "Kafka", C_MSG, "application-layer/kafka.md"),
    ("xmpp", 880, 100, "XMPP", C_MSG, "application-layer/xmpp.md"),
    ("smb", 880, 140, "SMB", C_MSG, "application-layer/smb.md"),
    ("netbios", 880, 180, "NetBIOS", C_MSG, "application-layer/netbios.md"),
    # VoIP / Media
    ("sip", 990, 60, "SIP", C_VOIP, "application-layer/sip.md"),
    ("rtsp", 990, 100, "RTSP", C_VOIP, "application-layer/rtsp.md"),
    ("sdp", 990, 140, "SDP", C_VOIP, "application-layer/sdp.md"),
    ("rtp", 1100, 60, "RTP", C_VOIP, "application-layer/rtp.md"),
    ("rtcp", 1100, 100, "RTCP", C_VOIP, "application-layer/rtcp.md"),
    ("webrtc", 1100, 140, "WebRTC", C_NAT, "application-layer/webrtc.md"),
    # Telecom apps
    ("smpp", 1460, 60, "SMPP", C_TELE, "application-layer/smpp.md"),
    ("wbxml", 1460, 100, "WBXML", C_TELE, "application-layer/wbxml.md"),
    ("eas", 1460, 140, "ActiveSync", C_TELE, "application-layer/eas.md"),
    ("syncml", 1570, 60, "SyncML", C_TELE, "application-layer/syncml.md"),
    ("mm5", 1570, 100, "MM5", C_TELE, "application-layer/mm5.md"),
    # IoT / Industrial
    ("modbus", 1690, 60, "Modbus", C_IOT, "industrial/modbus.md"),
    ("profibus", 1690, 100, "PROFIBUS", C_IOT, "industrial/profibus.md"),
    ("dds", 1690, 140, "DDS/ROS2", C_IOT, "application-layer/dds.md"),
    ("dmx", 1800, 60, "DMX512", C_IOT, "bus/dmx512.md"),
    ("midi", 1800, 100, "MIDI", C_IOT, "bus/midi.md"),
    # Sync
    ("syncml2", 440, 180, "SyncML", C_INFRA, "application-layer/syncml.md"),
    ("bgp_app", 550, 180, "BGP", C_INFRA, "application-layer/bgp.md"),
]

for pid, px, py, plbl, pcol, ppath in protos_l7:
    r, t = make_rect(pid, px, py, BW, BH, pcol[0], pcol[1], plbl, FS, gh(ppath))
    elements.extend([r, t])

# ============================================================
# LAYER 6 - SECURITY / PRESENTATION
# ============================================================

protos_l6 = [
    ("tls", 1240, 240, "TLS 1.3", C_SEC, "application-layer/tls.md"),
    ("dtls", 1240, 280, "DTLS", C_SEC, "application-layer/dtls.md"),
    ("srtp", 1350, 240, "SRTP", C_SEC, "application-layer/srtp.md"),
    ("ice", 990, 240, "ICE", C_NAT, "application-layer/ice.md"),
    ("stun", 1100, 240, "STUN", C_NAT, "application-layer/stun.md"),
    ("turn", 1100, 280, "TURN", C_NAT, "application-layer/turn.md"),
    ("spf", 440, 240, "SPF", C_AUTH, "application-layer/spf.md"),
    ("dkim", 550, 240, "DKIM", C_AUTH, "application-layer/dkim.md"),
    ("dmarc", 660, 240, "DMARC", C_AUTH, "application-layer/dmarc.md"),
    ("dane", 770, 240, "DANE", C_AUTH, "application-layer/dane.md"),
    ("wg_sec", 1240, 280, "WireGuard", C_VPN, "application-layer/wireguard.md"),
]

for pid, px, py, plbl, pcol, ppath in protos_l6:
    r, t = make_rect(pid, px, py, BW, BH, pcol[0], pcol[1], plbl, FS, gh(ppath))
    elements.extend([r, t])

# ============================================================
# LAYER 4 - TRANSPORT
# ============================================================

protos_l4 = [
    ("tcp", 200, 350, "TCP", ("#b2f2bb", "#15803d"), "transport-layer/tcp.md"),
    ("udp", 350, 350, "UDP", ("#b2f2bb", "#15803d"), "transport-layer/udp.md"),
    ("quic", 500, 350, "QUIC", ("#b2f2bb", "#15803d"), "transport-layer/quic.md"),
    ("sctp", 650, 350, "SCTP", ("#b2f2bb", "#15803d"), "transport-layer/sctp.md"),
]

for pid, px, py, plbl, pcol, ppath in protos_l4:
    r, t = make_rect(pid, px, py, 130, 40, pcol[0], pcol[1], plbl, 20, gh(ppath))
    elements.extend([r, t])

# ============================================================
# LAYER 3 - NETWORK
# ============================================================

protos_l3 = [
    ("ipv4", 170, 460, "IPv4", ("#fff3bf", "#b45309"), "network-layer/ip.md"),
    ("ipv6", 310, 460, "IPv6", ("#fff3bf", "#b45309"), "network-layer/ipv6.md"),
    ("icmp", 450, 460, "ICMP", ("#fff3bf", "#b45309"), "network-layer/icmp.md"),
    ("igmp", 560, 460, "IGMP", ("#fff3bf", "#b45309"), "network-layer/igmp.md"),
    ("ospf", 170, 510, "OSPF", ("#fff3bf", "#b45309"), "network-layer/ospf.md"),
    ("isis", 280, 510, "IS-IS", ("#fff3bf", "#b45309"), "network-layer/isis.md"),
    ("mpls", 390, 510, "MPLS", ("#fff3bf", "#b45309"), "network-layer/mpls.md"),
    ("vrrp", 500, 510, "VRRP", ("#fff3bf", "#b45309"), "network-layer/vrrp.md"),
    # VPN/Tunnel at L3
    ("ipsec", 1240, 460, "IPsec", C_VPN, "network-layer/ipsec.md"),
    ("gre", 1350, 460, "GRE", C_VPN, "network-layer/gre.md"),
    ("l2tp", 1240, 510, "L2TP", C_VPN, "tunneling/l2tp.md"),
    ("vxlan", 1350, 510, "VXLAN", C_VPN, "tunneling/vxlan.md"),
    ("geneve", 1460, 460, "Geneve", C_VPN, "tunneling/geneve.md"),
    ("gtp", 1460, 510, "GTP", C_VPN, "tunneling/gtp.md"),
    # Telecom L3
    ("ss7", 1570, 460, "SS7", C_TELE, "telecom/ss7.md"),
    ("isdn", 1570, 510, "ISDN", C_TELE, "telecom/isdn.md"),
]

for pid, px, py, plbl, pcol, ppath in protos_l3:
    r, t = make_rect(pid, px, py, BW, BH, pcol[0], pcol[1], plbl, FS, gh(ppath))
    elements.extend([r, t])

# ============================================================
# LAYER 2 - DATA LINK
# ============================================================

protos_l2 = [
    ("eth", 170, 600, "Ethernet", C_L2, "link-layer/ethernet.md"),
    ("arp", 290, 600, "ARP", C_L2, "link-layer/arp.md"),
    ("ppp", 400, 600, "PPP/PPPoE", C_L2, "link-layer/ppp.md"),
    ("vlan", 510, 600, "802.1Q", C_L2, "link-layer/vlan8021q.md"),
    ("stp", 620, 600, "STP", C_L2, "link-layer/stp.md"),
    ("lldp", 730, 600, "LLDP", C_L2, "link-layer/lldp.md"),
    ("lacp", 730, 645, "LACP", C_L2, "link-layer/lacp.md"),
    # Industrial buses at L2
    ("can", 1700, 600, "CAN", C_IOT, "bus/can.md"),
    ("i2c", 1810, 600, "I2C", C_IOT, "bus/i2c.md"),
    ("spi", 1920, 600, "SPI", C_IOT, "bus/spi.md"),
    ("i2s", 1810, 645, "I2S", C_IOT, "bus/i2s.md"),
    ("onewire", 1920, 645, "1-Wire", C_IOT, "bus/onewire.md"),
    ("usb", 1700, 645, "USB", C_IOT, "bus/usb.md"),
    # Wireless at L2
    ("wifi", 1960, 600, "802.11", C_WIRE, "wireless/80211.md"),
    ("mesh", 2070, 600, "802.11s", C_WIRE, "wireless/80211s.md"),
    ("bt", 1960, 645, "Bluetooth", C_WIRE, "wireless/bluetooth.md"),
    ("zigbee", 2070, 645, "Zigbee", C_WIRE, "wireless/zigbee.md"),
    ("zwave", 2070, 690, "Z-Wave", C_WIRE, "wireless/zwave.md"),
    ("nfc", 1960, 690, "NFC", C_WIRE, "wireless/nfc.md"),
]

for pid, px, py, plbl, pcol, ppath in protos_l2:
    r, t = make_rect(pid, px, py, BW, BH, pcol[0], pcol[1], plbl, FS, gh(ppath))
    elements.extend([r, t])

# ============================================================
# LAYER 1 - PHYSICAL
# ============================================================

protos_l1 = [
    ("t1", 1460, 755, "T1/DS1", C_L1, "telecom/t1.md"),
    ("e1", 1570, 755, "E1", C_L1, "telecom/e1.md"),
    ("xdsl", 1460, 800, "xDSL", C_L1, "telecom/xdsl.md"),
    ("docsis", 1570, 800, "DOCSIS", C_L1, "telecom/docsis.md"),
    ("rs485", 1700, 755, "RS-485", C_L1, "serial/rs485.md"),
    ("rs232", 1810, 755, "RS-232", C_L1, "serial/rs232.md"),
    ("rs422", 1700, 800, "RS-422", C_L1, "serial/rs422.md"),
    ("uart", 1810, 800, "UART", C_L1, "serial/uart.md"),
]

for pid, px, py, plbl, pcol, ppath in protos_l1:
    r, t = make_rect(pid, px, py, BW, BH, pcol[0], pcol[1], plbl, FS, gh(ppath))
    elements.extend([r, t])

# ============================================================
# KEY ARROWS (encapsulation relationships)
# ============================================================

arrows = [
    # HTTP -> TCP
    ("a1", 230, 200, 0, 150, "#4a9eed"),
    # TCP -> IPv4
    ("a2", 260, 390, 0, 70, "#15803d"),
    # UDP -> IPv4
    ("a3", 400, 390, 0, 70, "#15803d"),
    # IPv4 -> Ethernet
    ("a4", 220, 495, 0, 105, "#b45309"),
    # RTP -> UDP
    ("a5", 1145, 180, -750, 175, "#8b5cf6"),
    # SIP -> TCP
    ("a6", 1040, 180, -790, 175, "#8b5cf6"),
    # MQTT -> TCP
    ("a7", 820, 180, -570, 175, "#22c55e"),
    # SS7 -> T1/E1
    ("a8", 1620, 555, 0, 200, "#8b5cf6"),
]

for aid, ax, ay, dx, dy, acol in arrows:
    elements.append(make_arrow(aid, ax, ay, dx, dy, acol))

# --- FOOTER ---
elements.append(make_text("footer", 700, 850,
    "github.com/yepher/world_of_protocols  |  105 protocols", 18, "#757575"))

# ============================================================
# BUILD EXCALIDRAW FILE
# ============================================================

excalidraw = {
    "type": "excalidraw",
    "version": 2,
    "source": "world-of-protocols",
    "elements": elements,
    "appState": {
        "viewBackgroundColor": "#ffffff",
        "gridSize": None,
    },
    "files": {},
}

output_path = "../maps/protocol-map.excalidraw"
with open(output_path, "w") as f:
    json.dump(excalidraw, f, indent=2)

print(f"Generated {output_path} with {len(elements)} elements")
print(f"Protocol boxes with GitHub links: {sum(1 for e in elements if e.get('link'))}")
