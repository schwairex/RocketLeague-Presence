# Verification — v0.2.6

Windows 11, Python 3.12.10, PyInstaller 6.22.3, 2026-10-06 (Europe/Istanbul).
Python 3.11+ is supported; Python 3.11 and Windows 10 were not separately exercised.
Historical evidence: [v0.2.5 verification](verification-v0.2.5.md).

- **233 pytest tests passed**, including **19 v0.2.6 regressions**. Before the
  formatter/priority fix, 18 of the 19 new cases failed; they passed afterwards.
  Real local TCP tests deliberately fragment and concatenate documented packets,
  reduce them into match state and publish to mocked Discord.
- Exact ranked details: `Ranked 2v2 • 🔵 5 - 2 🟠`; state:
  `⚽1  🧤2  ⭐593` (two spaces between stats). Casual uses its actual mode name,
  the same stats-only state and no small artwork/tooltip. Training sends
  `Training` and `Mannfield (Night)`, without stats, small assets or timestamps.
  Ranked/casual arena names appear only in large artwork tooltips. Selected
  current-mode rank stays in small artwork/tooltip, never in text.
- Countdown, goal replay and pause retain the stats line, omit both ticking
  timestamp fields and send no static white clock or kickoff/replay label.
  RoundStarted restores the live native countdown. Overtime retains its start
  timestamp while active; stopped overtime excludes paused time on resumption.
  The existing single overtime policy and v0.2.5 ordering regressions remain.
- Personal goal/save/score changes bypass the ordinary four-second coalescing
  delay when an activity write is available. Burst tests prove they cannot
  exceed the unchanged rolling five-writes-per-20-seconds budget; the newest
  value replaces queued intermediates. Unchanged payloads are skipped.
- Missing player identity/fields display `—`; actual zero is `0`. Explicit
  unmatched identity never borrows an opponent's stats. Hiding player stats
  omits the state field instead of showing an unrelated map/clock. The UI
  preview also respects that omitted field. Privacy toggles and text limits pass.
- Actual pypresence IPC serialization has the exact stats text, map/rank keys
  and tooltips; active ranked → stopped casual removes old small artwork and
  timestamps. UTF-8 frame length agrees with actual encoded bytes.
- Independent read-only review reported no actionable findings; **55 focused
  tests passed**, including all 19 new cases and related lifecycle/publisher tests.
- Browser sample-data QA: [ranked](images/v026-ranked.png),
  [casual](images/v026-casual.png), [training](images/v026-training.png),
  [stopped](images/v026-stopped.png) and [unknown](images/v026-unknown.png).
  Exact DOM text includes the two spaces; the stopped preview timer is empty.
  English and Turkish Appearance screenshots were updated in place. No browser
  console warning/error was observed. These are app previews, not real Discord.
- Final frozen EXE: GUI subsystem 2, embedded icon, 1120×760 startup, offline
  assets, fixed/read-only application ID, legacy settings migration, healthy
  v0.2.6 startup acknowledgment and English persistence passed. Fresh Turkish
  defaults contain eight independent rank choices. No captured GUI ERROR logs.
- Native Windows sizing: eight edge/corner hit tests passed; minimum 900×640.
  All five tabs passed at 900×640, 1120×760, 1400×900 and maximized 2560×1392
  without horizontal overflow. Save/Cancel remain limited to editable tabs.
  The isolated smoke test now waits for asynchronous maximize/minimum resizing
  before measuring it; this does not change normal application behavior.
- Report submission/loading/success and field clearing passed through the real
  JS/Python bridge with injected HTTP 200 in both languages; no public report
  was submitted. The unchanged updater retains prior native replacement/rollback
  evidence and the final EXE acknowledges healthy startup.
- Both README designs, folder organization and original logo are preserved.
  Original logo bytes match the archived v0.2.5 source. The two Appearance
  screenshots, version badges, usage guides and changelog are updated in place.
  All 80 relative documentation links/anchors and self-contained SVG checks pass.
- Source/Windows ZIPs use standard DEFLATE and ZIP 2.0. Fully closed archives
  pass CRC and complete byte comparison before atomic replacement. Windows
  Shell.Application opens both; Expand-Archive extracts both successfully.
  All 107 source files and all 52 Windows package files match their originals;
  all previous v0.2.5 source paths remain. The extracted source passes all
  233 tests. SHA-256 files accompany the EXE and both archives. Live settings,
  logs, caches and build intermediates are excluded from the source package.

Reproduce:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m pytest rocket_league_rpc/tests/test_v026.py -v
python -m pytest rocket_league_rpc/tests/test_e2e.py rocket_league_rpc/tests/test_v2_e2e.py -v
.\build.ps1 -Python python
```

Discord's [timestamp schema](https://docs.discord.com/developers/events/gateway-events#activity-object-activity-timestamps)
has start/end and no pause field. Stopped phases therefore omit timestamps;
the native countdown returns when play resumes. A green paused timer cannot
be represented by this payload. Very rapid transitions can still wait for the
rolling activity budget. Unlimited instant updates or zero latency are not promised.

The [official Stats API](https://www.rocketleague.com/developer/stats-api) is the
only runtime game source. Rank/detailed menu states remain manual; arena/playlist
tables and local Target detection are best effort. Set the in-game name/platform
or PrimaryId to identify your own stats. No rank/arena keys or dependencies were
added in this release. The existing asset upload list remains in
[art-assets.md](../art-assets.md). No Portal uploads or public reports were made.
Real Discord rendering, live-game event ordering and overtime TimeSeconds
direction were not verified here. Real game INIs and the Discord pipe were not
modified during QA. Release publishing remains separate.
