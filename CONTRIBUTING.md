# Contributing

Thanks for helping make ONVIF fleet inventory better. The fastest way to
contribute is not code — it is evidence.

## 1. Report your cameras (no code needed)

Run a scan on your LAN and open a **Device report** issue with the JSON
report attached:

```sh
PYTHONPATH=src python3 -m onvifscan scan --user <your-onvif-user>
```

Reports from cameras we do not own are how vendor coverage grows:
a brand/firmware whose Scopes, capabilities or profiles parse wrong is a
bug — please file it with the report attached.

**Privacy check before posting**: reports contain IP addresses, MAC
addresses and serial numbers of *your* cameras (that is what an
inventory is). Redact anything you do not want public; keep the
manufacturer/model/firmware and the findings — those are the valuable
parts. Passwords are never in a report by construction (URIs are
masked and the output is scrubbed), but check anyway.

## 2. Code contributions

- Python standard library only — no new runtime dependencies.
- The tool stays **read-only**: PRs adding any non-`Get*` ONVIF call,
  PTZ movement, or configuration change will be declined.
- **No credential guessing, ever**: no default-password lists, no
  "try common passwords" features, no retry loops on auth failure.
  PRs in that direction will be declined on sight.
- Finding IDs and report schema fields are stable (they are anchors for
  the documentation); changing one needs a migration note.
- Tests: parser changes need fixture-based tests; behaviour changes
  should extend the personas in `tests/sim_device.py` rather than mock.
- Run the suite before opening a PR:

```sh
python3 -m pip install pytest
python3 -m pytest -q
```

## 3. Ground rules

- Never commit real credentials, captures from networks you do not own,
  or sample data from proprietary products of any vendor.
- Simulated fixtures use fictional brands and the obvious fixture
  password; keep it that way.
