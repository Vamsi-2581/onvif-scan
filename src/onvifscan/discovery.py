"""WS-Discovery: multicast/unicast Probe -> ProbeMatches parsing and merging.

Only discovery lives here. Everything after discovery (SOAP inventory)
is in scan.py. No credentials exist at this layer: WS-Discovery is
unauthenticated by design, and what a device broadcasts (Scopes, XAddrs)
is recorded verbatim.
"""
import select
import socket
import struct
import time
import uuid
import xml.etree.ElementTree as ET

MULTICAST_GROUP = "239.255.255.250"
DISCOVERY_PORT = 3702

PROBE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
 xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
 xmlns:dn="http://www.onvif.org/ver10/network/wsdl"
 xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
 <s:Header><wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
 <wsa:MessageID>urn:uuid:{mid}</wsa:MessageID>
 <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To></s:Header>
 <s:Body><d:Probe>{types}</d:Probe></s:Body></s:Envelope>"""

# Some devices only answer one of these two Probe shapes; send both.
PROBE_TYPES = ["<d:Types>dn:NetworkVideoTransmitter</d:Types>", ""]


def build_probe(types_xml):
    return PROBE_TEMPLATE.format(mid=str(uuid.uuid4()), types=types_xml).encode()


def _local_name(el):
    return el.tag.split("}")[-1]


def parse_probe_matches(data):
    """Parse one UDP packet into a list of ProbeMatch dicts (may be empty)."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return []
    matches = []
    for m in root.iter():
        if _local_name(m) != "ProbeMatch":
            continue

        def txt(suffix):
            for el in m.iter():
                if _local_name(el) == suffix:
                    return (el.text or "").strip()
            return None

        matches.append({
            "endpoint": txt("Address"),
            "types": txt("Types"),
            "scopes": txt("Scopes"),
            "xaddrs": (txt("XAddrs") or "").split(),
            "metadata_version": txt("MetadataVersion"),
        })
    return matches


def iface_ipv4():
    """[(name, ipv4)] for local interfaces (Linux ioctl; best effort)."""
    out = []
    try:
        import fcntl
    except ImportError:
        return out
    for _idx, name in socket.if_nameindex():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            packed = fcntl.ioctl(s.fileno(), 0x8915, struct.pack("256s", name.encode()[:15]))
            out.append((name, socket.inet_ntoa(packed[20:24])))
        except OSError:
            pass
        finally:
            s.close()
    return out


def discover(ifaces=None, timeout=5.0, port=DISCOVERY_PORT, directed=None):
    """Run WS-Discovery.

    ifaces: [(name, ip)] to send multicast probes from; None = auto-detect
    (loopback excluded unless it is the only interface).
    directed: [(host, port)] extra unicast probe targets (cross-VLAN use,
    or a device whose multicast is filtered).
    Returns (devices, meta). Devices are merged across responses.
    """
    if ifaces is None:
        all_ifaces = iface_ipv4()
        real = [(n, ip) for n, ip in all_ifaces if not ip.startswith("127.")]
        ifaces = real if real else all_ifaces
    sockets = []
    meta = {"interfaces": [n for n, _ip in ifaces], "subnets": [], "probe_count": 0}

    def new_sock(bind_ip):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((bind_ip, 0))
        s.setblocking(False)
        sockets.append(s)
        return s

    try:
        for _name, ip in ifaces:
            s = new_sock(ip)
            try:
                s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip))
            except OSError:
                pass
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
            for t in PROBE_TYPES:
                try:
                    s.sendto(build_probe(t), (MULTICAST_GROUP, port))
                    meta["probe_count"] += 1
                except OSError:
                    pass
            parts = ip.split(".")
            meta["subnets"].append(".".join(parts[:3]) + ".0/24")
        if directed:
            s = new_sock("")
            for host, dport in directed:
                for t in PROBE_TYPES:
                    try:
                        s.sendto(build_probe(t), (host, dport))
                        meta["probe_count"] += 1
                    except OSError:
                        pass
        raw = []  # (match_dict, source_ip)
        deadline = time.time() + timeout
        while time.time() < deadline and sockets:
            wait = max(0.0, deadline - time.time())
            ready, _w, _x = select.select(sockets, [], [], wait)
            if not ready:
                break
            for s in ready:
                try:
                    data, addr = s.recvfrom(65535)
                except OSError:
                    continue
                for m in parse_probe_matches(data):
                    m["source_ip"] = addr[0]
                    raw.append(m)
    finally:
        for s in sockets:
            s.close()
    return merge_matches(raw), meta


def merge_matches(raw):
    """Merge ProbeMatches of the same device (same EndpointReference).

    A device may answer several probes, from several addresses, with
    several XAddrs. Keep every XAddr, prefer the richest Scopes string.
    """
    by_key = {}
    order = []
    for m in raw:
        key = m.get("endpoint") or (m["xaddrs"][0] if m["xaddrs"] else m.get("source_ip"))
        if not key:
            continue
        if key not in by_key:
            by_key[key] = {"endpoint": m.get("endpoint"), "types": m.get("types"),
                           "scopes": m.get("scopes") or "", "xaddrs": [],
                           "metadata_version": m.get("metadata_version"),
                           "source_ips": []}
            order.append(key)
        dev = by_key[key]
        for x in m["xaddrs"]:
            if x not in dev["xaddrs"]:
                dev["xaddrs"].append(x)
        if len(m.get("scopes") or "") > len(dev["scopes"]):
            dev["scopes"] = m["scopes"]
        if m.get("source_ip") and m["source_ip"] not in dev["source_ips"]:
            dev["source_ips"].append(m["source_ip"])
    return [by_key[k] for k in order]
