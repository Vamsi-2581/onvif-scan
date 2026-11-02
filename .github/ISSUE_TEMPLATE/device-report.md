---
name: Device report
about: Share a scan report from real cameras (the most valuable contribution)
labels: device-report
---

**Camera(s)**: manufacturer / model / firmware (from the report is fine)

**How you ran it**: command line (redact credentials!), wired/Wi-Fi, with or without `--creds`

**What looked wrong or interesting**: fields missing, findings you did not expect, profiles that parsed oddly…

**Report**: attach `onvif-inventory.json` (check it first — it contains your cameras' IPs/MACs/serials; redact what you must, keep manufacturer/model/firmware/findings).

Note: reports can never contain passwords — stream URIs are masked and output is scrubbed. If you ever find one in a report, treat it as a critical bug and say so in the title.
