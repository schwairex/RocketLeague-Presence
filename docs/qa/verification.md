# Verification — v0.2.7

Windows 11, Python 3.12.10, PyInstaller 6.22.3, .NET Framework C# compiler,
2026-10-06. Python 3.11/Windows 10 were not separately exercised.
Historical evidence: [v0.2.6](verification-v0.2.6.md).

- **276 tests passed**, including 43 new identity/probe/restart regression cases.
  Initial provider/integration/restart tests were observed failing before the
  corresponding implementation. Four final-review findings were independently
  reproduced RED and fixed GREEN: cache origin, real-packet-only Target voting,
  sticky explicit spectator state and scalar VDF entry guard.
- Identity fixtures cover BOM/CRLF/malformed/missing VDF, ActiveUser conversion,
  sanitized Epic parameters, AccessDenied, Unicode/clan tags, stale IDs,
  cross-platform/duplicate names, account switches and low-confidence voting.
  New MockStatsServer tests use fragmented, concatenated, JSON-string Data
  over real loopback TCP, with no configured name/ID. Own goals/saves/points
  resolve against provider ID even when persona/game names differ. An unresolved
  identity omits the personal line entirely. Burst/coalescing still obeys the
  unchanged five writes in a rolling 20 seconds; normal changes wait >=4 s.
- Read-only local probe: Steam running, ActiveUser readable, converted ID matched
  loginusers.vdf's one account; no MostRecent flag. No RocketLeague.exe or real
  UpdateState was available. [Redacted observations](identity-probe.json),
  [provider/privacy limits and manual checks](../identity.md).
- **Root cause reproduced in a real PyInstaller one-file parent:** inherited
  _PYI_APPLICATION_HOME_DIR/_PYI_ARCHIVE_FILE reused the old runtime after its
  _MEI folder was removed. The restarted child exited -1 with missing python312.dll.
  The new pre-interpreter Windows launcher embeds/checksums the frozen core,
  clears stale runtime variables and launches independently. Settings/update
  paths stay beside the outer EXE; only runtime goes into per-user SHA cache.
- Native update proof used the **exact v0.2.4 updates.py from its source ZIP**,
  compiled into a real frozen parent (not a dummy C# parent), with the old helper
  unchanged. It upgraded to the real v0.2.7 GUI after the old _MEI disappeared.
  The production new-helper/outer-launcher upgrade also passed. An actual frozen
  failed-start EXE exited 17; the helper restored and restarted the production
  app. All preserved language/name/rank/update-interval preferences and migrated
  schema 3→4. [Native update results](updater-native.json).
  Release fetch/download HTTP is mocked for isolation; no GitHub release was
  published and no live report was submitted.
- Final EXE: GUI subsystem 2, embedded original icon, native pywebview bridge,
  health acknowledgement v0.2.7 and no captured GUI ERROR. Account status works
  in English and Turkish; fields appear only under General → Advanced, default
  auto. Read-only Discord application identity remains fixed. Fresh Turkish
  startup retains all eight rank defaults and mocked report loading/success.
- Five tabs passed at 900×640, 1120×760, 1400×900 and maximized 2560×1392, with
  eight native resize hit tests and no horizontal overflow. Appearance/General
  alone show Save/Cancel. [Detailed desktop results](release-smoke.json).
- README layout, branding logo and old file paths are preserved; local Markdown
  links/anchors and SVG assets validated. [Changed files](v027-changed-files.json).
  Packaging helpers create completely closed atomic standard-DEFLATE ZIPs;
  Windows Shell opening and Expand-Archive passed for both packages, with
  every extracted byte matching and all 276 extracted-source tests passing.
  All previous source file paths are preserved. SHA256SUMS accompanies delivery.

Commands:

```powershell
python run.py --identity-probe
python -m pytest
python -m pytest rocket_league_rpc/tests/test_v027_identity.py -v
.\build.ps1 -Python python
```

Real Discord rendering, live-game player-ID correlation, Epic parameter spelling,
elevated game access, Steam offline mode and overtime TimeSeconds direction remain
**UNVERIFIED**. Target is viewed-car inference and explicitly low confidence.
See [five live acceptance checks](../identity.md#manual-acceptance-checks).
No real game INI, authentication value or Discord IPC was touched by native QA.
