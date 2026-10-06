# Verification — v0.2.5

Windows 11, Python 3.12.10, PyInstaller 6.22.3, 2026-10-06 (Europe/Istanbul).
Python 3.11+ is supported; 3.11 and Windows 10 were not separately exercised.
Historical evidence: [v0.2.4 verification](verification-v0.2.4.md).

- **214 pytest tests passed**, including **25 v0.2.5 regressions** and real local
  TCP mock-server E2E with fragmented/concatenated packets and mocked Discord.
- Original stale goal timestamp reproduced before implementation: 20 of the
  initial 21 v0.2.5 cases failed, then passed after correction. GoalScored,
  replay flag/events, skipped replays, countdown and explicit pauses omit both
  timestamp fields; their last remaining time stays static. RoundStarted creates
  a fresh end timestamp. GoalTime is not misread as time remaining.
- Overtime pause/resume excludes stopped time. Independent review reproduced
  late overtime flags during/after a pause and a paused zero-time kickoff that
  created a future timestamp. Each ordering was added as a failing regression,
  then fixed; the final focused independent review passed 46 tests with no
  remaining findings. The single overtime policy stays in overtime_clock_start.
- Ranked text matches `Ranked 2v2 • 🔵 5 - 2 🟠` and
  `Mannfield (Night) • ⚽1 🧤2 ⭐593`; selected current-mode rank stays in small
  artwork/tooltip only. Casual uses its actual mode name and omits small assets.
  Training shows only Training/map. Hidden/unselected rank omits small assets.
  Privacy toggles, unknown stats and text limits remain covered.
- Real pypresence serialization: UTF-8 frame length agrees with actual bytes;
  switching ranked active → casual stopped removes old small artwork and all
  timestamps from the replacement SET_ACTIVITY message.
- Browser fixture: ranked/casual/training/stopped cards visually inspected.
  Frozen time is `⏸ 2:33`, without a live preview timer. Both interface languages
  retain the same layout; no browser console warning/error was observed.
  Updated Appearance screenshots and four QA captures use isolated sample data.
- Frozen EXE: GUI subsystem 2, embedded icon, 1120×760 startup, offline UI,
  fixed/read-only application identity, legacy settings migration, English
  persistence, Turkish fresh defaults, eight per-mode rank defaults and healthy
  v0.2.5 startup acknowledgment passed. No captured GUI ERROR logs.
- Native Windows sizing: hit tests **13,12,14,10,11,16,15,17**; minimum
  **900×640**. All five tabs have no horizontal overflow at 900×640,
  1120×760, 1400×900 and maximized 2560×1392 on this host. Save/Cancel remain
  restricted to editable tabs.
- Report form tested through the real JS/Python bridge and ReportClient with
  injected HTTP 200 responses in both languages. Loading lock, automatic
  version/OS, User-Agent, thanks and field clearing passed. No public issue was
  created. The unchanged updater retains previous native replacement/rollback
  evidence; the new EXE acknowledges healthy startup.
- Existing logo, README hero/style and folder organization are preserved.
  Logo bytes match the archived v0.2.4 source. Both README pages, download
  version badges, usage/artwork guidance and changelog are extended in place.
  Relative documentation links/anchors and self-contained SVG safety pass.
- Source/Windows ZIPs use standard DEFLATE and ZIP 2.0, without live config,
  logs or caches. Closed archives pass CRC and full byte comparisons before
  atomic replacement. Windows Shell.Application opens both packages;
  Expand-Archive extracts the source, all **100 files** match the source tree,
  and the extracted application passes all **214 tests**. SHA-256 manifests
  accompany the EXE and archives.

Reproduce:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m pytest rocket_league_rpc/tests/test_v025.py -v
python -m pytest rocket_league_rpc/tests/test_e2e.py rocket_league_rpc/tests/test_v2_e2e.py -v
.\build.ps1 -Python python
```

Discord's [timestamp schema](https://docs.discord.com/developers/events/gateway-events#activity-object-activity-timestamps)
has start/end and no pause field. Stopped game phases therefore use **static
remaining-time text**, then restore the live native countdown when play resumes.
This is not a native green paused timer. Very rapid transitions can still wait
for the unchanged rolling activity budget; zero transport latency is not promised.

The [official Stats API](https://www.rocketleague.com/developer/stats-api) is the
only runtime game source. Rank/detailed menus remain manual; Arena/Playlist
tables and local Target detection are best effort. Rank keys are prepared; no
Portal uploads were made. Real Discord rendering, live-game event order and
overtime TimeSeconds direction were not verified here. Real game INIs and the
Discord pipe were not modified during QA. Release publishing remains separate.
