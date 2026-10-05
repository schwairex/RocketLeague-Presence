# Verification — v0.2.0

Verified on Windows 11 with Python 3.12.10, 2026-10-05. Python 3.11 is supported by the source but was not separately exercised on this host.

- Final pytest: **86 passed** (1.47 s), including the original 53 regression tests, manual rank/activity configuration, player statistics, hot reload, training, encoded Data, malformed envelopes and GUI worker shutdown.
- Both end-to-end wire formats passed: documented object Data and real Windows JSON-string Data. Real ephemeral TCP listeners deliberately split/concatenate the full mock match; a mocked Discord client verifies the lifecycle, fields, Win result and minimum 15-second activity-write interval.
- The original menu-stuck bug was reproduced using a real, read-only Rocket League connection: outer Event was UpdateState, but Data was a JSON string. After normalization, real packets produced TRAINING, Arena Stadium_P, PlaylistId 9 and approximately 30 packets/second. No game commands were sent and the game was not restarted by verification.
- Native source GUI and the **actual frozen EXE** loaded WebView2, exposed the intended bridge, reported exactly **1120 × 760** client pixels, loaded no remote UI resources, had no GUI ERROR log entries, and closed cleanly. PE subsystem is 2 (Windows GUI), so the EXE does not open a console.
- release-smoke.json records sanitized frozen-build results. Smoke runs used a separate test mutex/config without Discord credentials, leaving the user's installed RPC alone. Production still shares one Windows-session mutex.
- Browser interactions verified: toggles, Cancel restoring edits, rank/division/manual activity save, menu/replay previews, four tabs, diagnostics open/close, and persistent Save/Cancel at 940 × 680. No JavaScript warning/error logs. See design-qa.md and its captured evidence.
- Independent read-only review found stale GUI draft and unhashable Event validation issues; both were fixed. Identity re-identification preserves existing clock/phase. Native/engine objects are private to the bridge.
- PyInstaller single-file windowed build succeeded. Source/Windows archives are integrity-checked; SHA-256 hashes are recorded alongside them.

Reproduce from source root:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m pytest rocket_league_rpc/tests/test_v2_e2e.py -v
.\build.ps1 -Python python
```

Limits: actual Discord Application ID/art uploads were not exercised. Rank and detailed menu/queue/shop status remain manual by the user's official-API-only choice. Playlist/arena variants and real overtime direction remain best effort; training TimeSeconds is not a match countdown. Windows .NET Framework 4.8 and WebView2 Runtime must be installed. Optional tray and automatic updater are not included. Real ini/user Discord settings were not modified during verification.
