# Verification — v0.2.3

Windows 11, Python 3.12.10, PyInstaller 6.22.3, 2026-10-05–06 (Europe/Istanbul).
Python 3.11+ is supported; 3.11 was not separately exercised on this host.

- **163 pytest tests passed**, including real TCP mock-server end-to-end tests
  with fragmented/concatenated packets and object/JSON-string Data envelopes.
- Per-mode rank migration, eight independent defaults, malformed config
  recovery, independent persistence/presence, eight renamed playlists, expanded
  arena lookups and longest-family matching are covered.
- Fake Steam/Epic installations verify discovery of both copies, backups and
  idempotent patching, active executable selection, partial permission errors,
  restart notices across RPC restarts and game relaunches, and startup when
  executable inspection is denied but process-name detection works.
- The actual pywebview Event class exercises the None-return loaded callback.
  Independent review found the incomplete first-run rank defaults; fixed and
  checked from both source and a fresh-config native EXE.
- Final frozen **rl-presence.exe** opened at **1120 × 760** with offline UI
  resources, fixed/read-only ID, embedded icons and working desktop bridge.
  English legacy-config migration and Turkish first run both rendered eight
  rank cards. No GUI ERROR logs were captured.
- The native report form used the real JS/Python bridge and ReportClient with
  an injected HTTP 200 sender. Loading/button lock, automatic version/OS,
  honest User-Agent, thanks text and field clearing passed in both languages.
- Real Worker reachability was verified through the production ReportClient
  with only malformed JSON on the wire: HTTP **400**, rather than the old
  Python-urllib HTTP 403 / Cloudflare 1010 response. **No public test report
  was created.** Successful public issue creation remains an external check.
- Local browser fixture QA verified rank Save/Cancel semantics, current-mode
  preview, Turkish/English labels, both developer profiles, responsive navigation
  while sending, HTTP 200/429/400 handling and retained error text. No JS
  warnings/errors or horizontal overflow at 1120x760 and 940x680.
- Existing regression coverage includes immutable app identity, training entry,
  goal-break anchor/kickoff resync, pause/overtime/end/replay lifecycle,
  five-write rolling budget/coalescing, parser/INI recovery and supervised shutdown.
- The production GitHubReleases client read the public v0.2.2/v0.2.1 EXE assets
  and SHA-256 digests. v0.2.3 is not uploaded by this delivery. Existing Windows
  update replacement/rollback evidence is retained in release-smoke.json;
  the final EXE independently acknowledged healthy v0.2.3 startup.
- Source/Windows archives include ART_ASSETS.md and exclude live config, logs
  and build caches. SHA-256 files accompany the release artifacts.

Reproduce from source:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m pytest rocket_league_rpc/tests/test_v2_e2e.py -v
.\build.ps1 -Python python
```

Limits: rank and detailed menu/shop/queue states remain manual because the
official Stats API does not supply them. Maps/playlists remain best effort;
104 exact Arena entries plus family matching do not guarantee all future maps.
UF_Night_P → United Futura is inferred from the installed package and official
Season 23 arena news. Discord artwork availability/rendering and real overtime
direction were not exercised. The native green timer cannot pause during goal
breaks; it is corrected at kickoff. Real game INIs and the real Discord pipe
were not modified during QA; installation tests used temporary game folders.
