# Verification — v0.2.4

Windows 11, Python 3.12.10, PyInstaller 6.22.3, 2026-10-06 (Europe/Istanbul).
Python 3.11+ is supported; 3.11 was not separately exercised on this host.

- **189 pytest tests passed**, including actual local TCP mock-server E2E with
  fragmented/concatenated packets, mocked Discord, lifecycle/timers, config,
  retry/coalescing, dual-install INI backups/discovery and report HTTP handling.
- Eight current-mode ranks select small artwork/tooltips, preserve map large
  artwork/name, and leave details/state clean. Unranked/casual/training/hidden
  rank fallback and the complete rank-key table are tested.
- Native resize tests cover eight edges/corners, negative coordinates, scaled
  borders and maximized behavior. Source and frozen EXE returned
  **13,12,14,10,11,16,15,17** from WM_NCHITTEST. Minimum clamps to **900×640**,
  startup remains **1120×760**, maximize uses **2560×1392** work area here.
  All five native tabs were checked at three sizes and maximized.
- Browser fixture: five tabs in Turkish/English at 900×640, 1120×760 and
  1600×1000, no horizontal overflow. Update/error phases, badges/categories,
  history state retention, safe text notes, About CTA, editable-only controls,
  live footer and keyboard focus passed. No JS warnings/errors.
- Both HTML references were captured and compared. Original fonts/palette/
  header retained; notes 13px/1.5, tags 78px, feature icons 32px, equal feature
  card heights. Sampled small-copy/tag/button contrast passes 4.5:1.
- Independent review found progress rounding to 100 before EOF. A failing
  regression reproduced it; streaming progress is now capped at 99. Only
  stage() signals 100 after closure/size checks immediately before hashing.
- Frozen EXE: GUI subsystem 2, embedded icon, offline assets, fixed/read-only
  identity, legacy config migration, Turkish first-run defaults, English
  persistence, health acknowledgment and no captured GUI ERROR logs.
- Native report uses real JS/Python bridge and ReportClient with injected HTTP
  200 sender. Loading lock, automatic version/OS, User-Agent, thanks and field
  clearing passed in both languages. **No public issue was created.** Successful
  live issue creation remains external; prior v0.2.3 invalid-only Worker
  reachability returned HTTP 400.
- Existing native updater replacement/healthy-startup rollback evidence is
  retained. Final EXE acknowledges healthy v0.2.4 startup. This delivery does
  not publish a GitHub release: upload EXE/checksum for automatic distribution.
- Source/Windows ZIPs exclude live config, logs and caches; include map/rank
  instructions and icon license, with CRC and SHA-256 verification.

Reproduce:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m pytest rocket_league_rpc/tests/test_v2_e2e.py -v
.\build.ps1 -Python python
```

Limits: rank/detailed menus remain manual; Arena/Playlist tables are best
effort. Rank keys are prepared; Portal images are not uploaded. Discord artwork
rendering, physical mouse drag across multiple DPI monitors and real overtime
direction were not exercised. Native hit-testing/sizing was exercised on Windows
11; Windows 10 was not separately tested. Discord's green timer cannot pause
during goal breaks and resyncs on kickoff. Real game INIs and Discord pipe were
not modified during QA; test folders and mocked clients were used.
