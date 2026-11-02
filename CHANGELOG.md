# Changelog

## v0.1.0 — 2026-11-02

First release.

- WS-Discovery inventory of a LAN: multicast probes on all interfaces
  (two probe shapes, 5 s window, TTL 1) plus directed `--host` probes
  and `--device-url` entries for multicast-filtered networks.
- Per-device read-only inventory: device clock offset (measured before
  any authentication), capabilities/services, device information,
  hostname, network interfaces, Media + Media2 profiles with encoder
  details, stream/snapshot URIs (password-masked), PTZ presence.
- WS-Security UsernameToken authentication signed against *device*
  time; one attempt per supplied credential per device; credentials
  from `--user`/`ONVIFSCAN_PASSWORD`/prompt or a `--creds` JSON map.
- Levels (FULL/PARTIAL/DISCOVERED_ONLY/UNREACHABLE) and findings with
  stable IDs: CLOCK_SKEW, UNAUTH_INFO_DISCLOSURE, UNAUTH_CAPS_DISCLOSURE,
  AUTH_FAILED, XADDR_MISMATCH, SCOPES_MINIMAL, MEDIA2_ONLY,
  LEGACY_MEDIA_ONLY, NO_PTZ, STREAM_URI_MISSING, RESPONSE_MALFORMED,
  CAPS_FALLBACK, NO_XADDR.
- JSON (schema 1) + single-file HTML reports; terminal summary;
  per-profile `rkdoctor rtsp …` next steps (RK Edge Doctor hand-off).
- Verified end-to-end against simulated strict/standard/legacy devices
  (in `tests/`); real-camera reports being collected.
