# Rocket League RPC implementation plan

Goal: a read-only Windows Python 3.11+ Discord presence companion driven only by the official local Stats API.

Architecture: asyncio transport feeds a defensive, immutable event reducer. A separate formatter builds current presence; one publisher owns Discord IPC, coalescing and the hard 15-second window. Process watching gates Stats connections and presentation. Installation/configuration is independent of match processing.

Source of truth: https://www.rocketleague.com/developer/stats-api (read 2026-10-05).
Architectural reference only: https://github.com/Its-Haze/league-rpc (module boundaries, lifecycle/reconnect UX, persisted preferences). No League data sources or logic.

Assumptions: overtime uses a local elapsed anchor, pending real clock samples; PlaylistId and Arena tables are unverified; Target is a viewed car, never proof of identity. Spectator fields and a manual spectating flag suppress target inference. Configured identity always wins.

Review focus: malformed/oversized streams; missing conditional fields; history playback emitting live events; disconnects while updates are pending; config/ini permission or syntax errors.

1. [x] Write and run parser, reducer, timestamp, lookup, configuration and ini tests against absent functionality; implement their modules and run tests.
2. [x] Write and run publisher/recovery/process/single-instance tests; implement the runtime, async IPC adapter and retry supervisors; run the suite.
3. [x] Write a TCP end-to-end test through StatsClient, reducer, formatter and mocked Discord IPC; implement the realistic mock server and verify split/concatenated messages.
4. [x] Add bilingual READMEs, complete exact asset-key documentation, console launcher and PyInstaller build script; verify CLI and build.
5. [x] Review requirements and failure paths, fix regressions with tests, run pytest plus explicit end-to-end check, and package the source.

Implementation proceeds in this chat as requested; no separate approval or git workflow is needed for this new projectless deliverable.
