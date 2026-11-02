# Vendor behaviour notes

What years of ONVIF integration pain look like, condensed. Each item is
either publicly documented vendor behaviour or reproduced by the
simulated devices in `tests/sim_device.py`. `onvif-scan` is designed
around every one of these; issue reports that confirm or extend this
table on real firmware are extremely welcome.

## Authentication and clocks

- ONVIF auth is WS-Security UsernameToken with
  `Digest = Base64(SHA1(rawNonce + Created + Password))`. Devices reject
  tokens whose `Created` is too far from **the device's own clock**
  (thresholds vary, seconds to minutes). Field cameras without NTP are
  routinely minutes to *hours* off. `GetSystemDateAndTime` is specified
  to work without authentication precisely so a client can measure the
  offset first — this tool always does, and signs with device time.
  A skewed clock is reported as `CLOCK_SKEW`; fix the camera's NTP.
- A rejected credential is tried **once**. Several vendors (notably
  Hikvision) lock accounts after repeated failures ("illegal login
  lock"); a scanner that retries can lock you out of your own fleet.

## ONVIF is often off, and its users are separate

- Hikvision firmware ≥ 5.5.0 ships ONVIF **disabled**; enabling it is a
  separate setting, and the ONVIF user list is **independent** of the
  web UI users (roles: Media / Operator / Administrator). A camera that
  "doesn't respond" or rejects the web admin password is usually this.
- Axis firmware ≥ 5.40 likewise ships ONVIF disabled; an ONVIF user and
  profile must be created first.
- Dahua and other vendors vary by firmware generation: older firmware
  may answer `GetDeviceInformation` with no authentication at all
  (reported as `UNAUTH_INFO_DISCLOSURE`), newer firmware is strict.
  Never assume by brand — the tool measures per device.

## Discovery quirks

- **Scopes completeness varies wildly.** Some devices broadcast
  name/hardware/MAC/location/Profile; others send a single Profile URI.
  Identity is therefore assembled in layers: Scopes →
  GetNetworkInterfaces (MAC) → report what is missing (`SCOPES_MINIMAL`).
- Some devices only answer a Probe with empty Types or `tds:Device`, not
  `dn:NetworkVideoTransmitter`. The tool sends both probe shapes.
- ProbeMatches arrive with randomised delay (by design) — a listen
  window under ~5 s silently loses devices.
- **XAddrs can be wrong** (dual NICs, NAT, IP changed without the ONVIF
  stack noticing). When the XAddr host differs from the responder, the
  report flags `XADDR_MISMATCH` and inventory falls back to the source
  IP on transport failure.
- Multicast is frequently filtered (Wi-Fi AP isolation, VLAN design).
  Zero results ≠ zero cameras. Use a wired interface, or `--host`.

## Media generations

- Newer devices may expose **Media2 only** (Profile T generation,
  `MEDIA2_ONLY`); older ones Media (ver10) only (`LEGACY_MEDIA_ONLY`).
  Profiles can differ between the two services on the same camera; the
  tool queries both and tags each profile with its generation.
- Stream URIs sometimes come back **with credentials embedded**. They
  are masked before they touch the report, and the final report is
  scrubbed of every password used in the scan.

## Sloppy XML

Real firmware ships unbound prefixes and missing namespace
declarations. The parser tolerates them (and flags `RESPONSE_MALFORMED`)
instead of dropping the device — and one bad device can never abort a
fleet scan.
