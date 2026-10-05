# Verification — v0.2.2

Windows 11, Python 3.12.10, PyInstaller 6.22.3, 2026-10-05. Python 3.11+
is supported; Python 3.11 was not separately exercised on this host.

- **136 pytest tests passed**, including both real TCP mock-server formats
  (object and JSON-string Data), fragmented/concatenated packets, match lifecycle,
  training, manual rank, config/INI recovery and GUI engine shutdown.

- v0.2.2 regressions verify the retained goal/replay/kickoff anchor, scoreboard
  changes during the break, kickoff resync and Rocket League name in every phase.
  A pypresence IPC wire test verifies the name and NAME status display type.
- Turkish/English UI selection persisted in the native EXE. Report an Issue
  follows About; no horizontal overflow at 1120x760 or 940x680. The full form
  and send button fit the default viewport. No browser JS errors/warnings.
- Report tests verify Worker-only endpoint, exact JSON keys, automatic version/OS,
  validation before IO, Unicode lengths, timeout, no redirects, concurrent-submit
  rejection, HTTP 200/429/400/500 and offline/unexpected failures. Browser mock QA
  verifies disabled/loading state, responsive tab navigation, success clearing,
  error retention and validation stopping requests. No real public report sent.
- Independent review found Unicode native-input/counter mismatch; removed UTF-16
  native limits so frontend and Python consistently validate code-point lengths.
- Prior regressions verify immutable ID, direct training entry, omitted training
  P/G/S, removed replay/time text, stable timestamps, five-write rolling budget,
  coalescing and delayed timestamp synchronization.
- Update tests cover version comparison, malformed/foreign assets, checksum
  fallback/mismatch, non-EXE/incomplete files, offline/source-run protection,
  relaunch config paths, notifications, failures and retry-loop prevention.
- Production Windows helper ran against locally compiled dummy EXEs: successful
  replacement/startup acknowledgement and failed-startup rollback. Both preserved
  config; rollback actually restarted the old executable. The verified release
  digest is carried into handoff and checked against the copied incoming EXE.
- Final frozen **rl-presence.exe** loaded WebView2 at **1120 × 760**, offline
  resources and working bridge; fixed ID tampering was ignored, old config
  migrated and healthy startup was acknowledged. No GUI ERROR logs.
- PE subsystem 2 confirms windowed launch; embedded icon/group-icon resources
  exist. The packaged ICO is also assigned to the WinForms window, with a
  dedicated AppUserModelID for taskbar branding.
- Browser QA checked Updates/About, immutable ID, GitHub failure/retry at
  1120 × 760 and 940 × 680. No horizontal overflow or JS warnings/errors.
  Screenshots show fixture data, not live GitHub release claims.
- Independent review findings were fixed: relative config relaunch, failed-update
  loops, startup-dialog rollback and digest handoff integrity.
- release-smoke.json records sanitized native results. Fake Discord adapters
  and a separate test mutex were used; no real Discord pipe was touched.

Reproduce from source:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m pytest rocket_league_rpc/tests/test_v2_e2e.py -v
.\build.ps1 -Python python
```

Limits: Discord's native green timer has no pause field; it advances across
goal breaks and is corrected at kickoff. Actual Discord rendering/art assets
were not exercised; name/timestamp payloads were verified on the IPC wire. Prior v0.2 real
read-only game packets verified JSON-string Data, Stadium_P and training ID 9.
Other playlist/arena values and real overtime direction remain best effort.
Rank/menu detail remains manual by the official-API-only choice. Real game INI
and installed user app were not modified. Supplied GitHub Releases API returned
404; live release discovery cannot be verified until the repository is public
and a Release exists. Local Windows update/handoff/rollback tests passed.
