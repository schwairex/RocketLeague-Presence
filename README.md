# rocket-league-rpc

Python 3.11+ Windows desktop companion for Rocket League Discord Rich Presence. It reads the **official local Stats API**; it does not inspect memory, call private game services or send game commands.

[Türkçe kullanım kılavuzu](README.tr.md) · [Official Stats API documentation](https://www.rocketleague.com/developer/stats-api) · [Discord Developer Portal](https://discord.com/developers/applications)

## Quick start

Extract the source into a writable folder, then in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Or run the built `rocket-league-rpc.exe` in a writable folder. The default `config.json` and `logs/` live beside `run.py` for source runs, or beside the executable for packaged runs. `--config path\config.json` selects another config file; logs still live beside the launcher.


## Desktop window (v0.2)

Close the old RPC before launching this version. Copy/keep your existing config.json beside the new EXE to preserve the Application ID. Windows 10/11, .NET Framework 4.8 and Microsoft Edge WebView2 Runtime are required. The EXE includes Python and the UI fonts/SVGs; the interface loads offline.

Görünüm retains the supplied design. Genel adds manual rank/division, main menu, queue, shop, free play, custom training and garage. These choices persist; real match telemetry takes priority. **The official API does not provide rank or detailed menu status.** A single manually selected rank is displayed across modes; it is not automatically refreshed.

Kaydet atomically applies settings without restarting RPC; İptal discards unsaved edits. Preview samples never publish to Discord. The live card and bug button open all players' Score/Goals/Saves, raw match fields, last received event, connection errors, pending payload and last sent payload. Genel can open logs or save logs/diagnostics.json. Status dots distinguish a disconnected socket, connection without packets, live telemetry and the game being closed.

The previous menu-stuck bug was reproduced with real TCP: Data arrived as a JSON-encoded string. v0.2 accepts both this form and the documented object after stream framing. Training TimeSeconds is available in diagnostics but is not labeled as match time remaining. Packet rate shown in the footer is measured, not assumed.

GUI mode remains open without client_id; enter it in Genel. Console mode exits with instructions when it is missing. Changes made by editing JSON outside the app require a restart. Use `--console --skip-install` for console-only diagnostic runs; the GUI setup button remains an explicit action.

## Discord application and images

1. Create an application in the [Developer Portal](https://discord.com/developers/applications), with a name such as **Rocket League**. Discord displays the application's name.
2. Enter its **Application ID** in the **Genel** tab and click **Kaydet**, or set `client_id` in JSON. No bot token, OAuth login or client secret is required.
3. In the application's Rich Presence / Art Assets area, upload images using the exact lowercase keys below. These are **every unique key used by `maps.py`**, plus the generic and team icons. Use artwork you have permission to use. Variants share their base arena image.
4. Start the Discord **desktop** app on this Windows session. Enable activity sharing in Discord's privacy settings if the activity is hidden.

| Exact asset key | Artwork |
|---|---|
| `rl_logo` | Generic Rocket League image |
| `blue` | Blue team icon |
| `orange` | Orange team icon |
| `dfh_stadium` | DFH Stadium |
| `beckwith_park` | Beckwith Park |
| `utopia_coliseum` | Utopia Coliseum |
| `wasteland` | Wasteland |
| `neo_tokyo` | Neo Tokyo |
| `urban_central` | Urban Central |
| `aquadome` | Aquadome |
| `mannfield` | Mannfield |
| `forbidden_temple` | Forbidden Temple |
| `farmstead` | Farmstead |

Missing uploaded assets do not affect the match text but the images may not appear. This distribution contains no arena artwork and no preconfigured Discord Application ID.

## First run and enabling the Stats API

The desktop window stays open on first run even with no Application ID. In **Genel**, enter your ID, select rank/division and your activity outside a match, then click **Kaydet**. In **Görünüm**, enter your game name/platform and save to enable personal points/goals/saves. Explicit PrimaryId takes priority; clear an old ID when changing accounts.

Click **Stats API’yi yapılandır** in **Genel**. The installer discovers Steam through registry/libraryfolders.vdf, or Epic through .item manifests (including Sugar). If discovery fails, enter the folder containing TAGame, save, then click again. Console mode retains its once-only install-path prompt.

The installer selects `<install>\TAGame\Config\TAStatsAPI.ini` when present; otherwise it selects/creates `DefaultStatsAPI.ini`. It ensures:

```ini
[TAGame.MatchStatsExporter_TA]
PacketSendRate=30
Port=49123
WebPort=49124
```

An existing positive packet rate up to 120 is preserved. Disabled/invalid rates become 30; rates above 120 become 120. Ports follow the config and must be nonzero and different. A `.bak` is written **before each needed patch**; later backups get a unique suffix. For a newly created file the empty backup records that no original existed. An unchanged ini is not rewritten. `configparser` preserves option case and unrelated sections/values, but a patch normalizes whitespace and drops comments; restore them from the backup if needed. UTF-8, BOM and common Windows encodings are supported. Malformed ini syntax is reported with the original left untouched.

**Fully quit and restart Rocket League after any patch**, including when the app warns that the game is already running. A successful ini edit cannot enable the API in an already running game. Permission errors suggest administrator privileges; moving the RPC app to a writable folder also helps config/log writes. `--skip-install` leaves discovery and patching to you.

The GUI waits for an Application ID in Genel; console mode exits with instructions if it is blank. The app retries Stats every 3–5 seconds and Discord with a capped 3–30 second backoff. Game stopped → clear presence; game running without a match → the selected manual activity, or `In menus / Queueing` when set to auto. The API cannot distinguish an actual queue from other menu activity.

## Configuration

Copy `config.example.json` if desired; first run also generates defaults. Restart the RPC app after editing config. Invalid JSON or a non-object root is backed up and regenerated; invalid field types fall back to defaults. Writes are atomic. A read-only config directory uses in-memory defaults and logs a clear error.

| Key | Default / meaning |
|---|---|
| `client_id` | `""`; your Application ID, required for RPC |
| `install_path` | `""`; discovery or one-time prompt |
| `player_name` | `""`; case-insensitive explicit local player name |
| `player_primary_id` | `""`; `Platform\|Uid\|Splitscreen`, preferred over name |
| `stats_host` | `127.0.0.1`; local Stats API host |
| `stats_port` | `49123`; TCP port, 1–65535 |
| `stats_web_port` | `49124`; optional WebSocket port, distinct from TCP |
| `stats_transport` | `"tcp"`; set `"websocket"` to opt into the alternative transport |
| `update_interval` | `15`; clamped to 15–3600 seconds |
| `log_level` | `"INFO"`; DEBUG / INFO / WARNING / ERROR / CRITICAL |
| `show_score`, `show_map`, `show_mode` | `true`; map off also removes map images/tooltips |
| `show_perspective` | `false`; show `You … Opp` when local team is known |
| `show_time` | `true`; controls timer text and timestamps |
| `show_rank`, `show_player_stats` | `true`; manual rank and local P/G/S |
| `rank_tier`, `rank_division` | `Unranked`, `1`; division is 1–4; SSL has none |
| `manual_activity` | `auto`; main_menu/menu/queue/shop/training/custom_training/garage |
| `player_platform` | `auto`; steam/epic filters name matching |
| `spectating` | `false`; set true when watching a live match to suppress Target inference |
| `auto_learn_primary_id` | `true`; persist ID learned **only from an explicit configured name** |
| `install_prompted` | `false`; remembers whether the manual path prompt was shown |

Explicit ID/name detection takes priority and never falls through to a viewed opponent when the configured player is missing. With no configured identity, `Game.Target` is used only when `bHasTarget` is true and spectator-only fields are not observed. **Target is the currently viewed car, not a local-user identifier.** Spectator detection is best effort; set `spectating: true` or configure your identity for reliable wording. When unknown the app uses Blue/Orange scores and a neutral winner. PlayerJoined lacks team data, so detection waits for UpdateState. PlayerLeft clears a departed player's identity until another snapshot supplies it.

## Match clocks and rate limiting

The reducer handles menu, countdown, active play, goal replay, pause, overtime, ended and history replay phases. It resets for a new online MatchGuid and treats an empty offline guid as one match until leave. `ReplayCreated` stays `Watching a replay` through live-shaped replay events and never shows a live score/timer. Scores are authoritative from UpdateState, not guessed from GoalScored (which may involve own goals).

RoundStarted synchronizes the live end timestamp; clock samples resynchronize only when they differ by **more than 2 seconds**. Countdown, goal replay (also immediately after GoalScored), pause and finished states have no ticking timestamp. A skipped replay can recover through CountdownBegin or `bReplay: false`. The final result expires after 60 seconds or on MatchDestroyed.

**Overtime direction is unverified.** The app uses an elapsed start anchor rather than deriving it from TimeSeconds. The first observed overtime kickoff establishes it; on a mid-overtime reconnect the first observed packet is a provisional anchor, so elapsed time can be incomplete. DEBUG logs include raw overtime TimeSeconds samples. `state.overtime_clock_start()` is the single policy function to change after real packets establish the direction.

All activity writes, including normal clears, are at least **15 seconds apart**, measured with a monotonic clock. Latest payload wins; unchanged payloads are skipped. Start/end transitions bypass a longer configured update interval when the 15-second floor permits. Failed writes consume the window too; reconnect resends the current state without resetting it. Fast phases or a start/end that both happen inside one window can be coalesced away. Discord can therefore display a previous phase for up to 15 seconds. On Ctrl+C, an eligible activity is cleared; otherwise the app closes the owning IPC connection without another activity write, removing its presence on disconnect.

## Debugging and test match

```powershell
.\.venv\Scripts\python.exe run.py --debug
.\.venv\Scripts\python.exe run.py --debug --raw-packets
```

`--debug` logs **every parsed raw event name**, including cheaply ignored events, and unexpected shapes. Full JSON is opt-in with `--raw-packets`, rotating in `logs/raw_packets.log` (10 MiB × 4 including current). `logs/app.log` is structured JSONL and rotates at 5 MiB × 4. Share these files and their numbered rotations, with a description of the problem and when it occurred. Raw logs contain player names and platform IDs; redact them before sharing if desired. No raw packets are logged at normal INFO level. Unbalanced corrupt JSON has no reliable delimiter; it is discarded when the bounded 2 MiB parser buffer fills. Balanced malformed objects are discarded individually.

To run a simulated match, **quit Rocket League** to free port 49123. In separate terminals:

```powershell
.\.venv\Scripts\python.exe -m rocket_league_rpc.mock_stats_server --port 49123 --delay 5
.\.venv\Scripts\python.exe run.py --mock-game --debug --raw-packets
```

You still need a valid client_id and desktop Discord for a visible manual test. The mock deliberately splits and concatenates exact documented envelopes. It replays countdown, regular clocks, a goal replay, pause, overtime, end/podium and leave. Its overtime TimeSeconds increases **as a simulation choice**, not evidence about the real API. The pytest end-to-end test needs neither Discord nor Rocket League: it uses a real ephemeral TCP listener and a mocked Discord client, advances injected clocks 15 seconds per event, and verifies the actual publisher's hard limit.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest rocket_league_rpc/tests/test_e2e.py -v
```

## Build and architecture

```powershell
.\build.ps1 -Python .\.venv\Scripts\python.exe -InstallDependencies
# Output: dist\rocket-league-rpc.exe
```

Build on Windows to obtain a Windows exe. The single-file build opens the supplied HTML design as a window, without a PowerShell/console window. The optional tray icon is not included. Source users can opt into console mode with `run.py --console`. There is one named mutex per Windows login session to prevent duplicate publishers; it is released automatically on process exit.

`config.py` owns validation/persistence; `installer.py` owns install discovery/ini changes; `game_watcher.py` owns process observation; `stats_client.py` owns read-only framing/transport; `state.py` is the reducer; `presence.py` formats fields; `rpc.py` owns async IPC and rate limiting; `runtime.py` owns supervisors/logging/instance lifetime; `main.py` wires them together. `maps.py` and `modes.py` are deliberately easy to extend.

The current [Its-Haze/league-rpc](https://github.com/Its-Haze/league-rpc) was reviewed **only for architecture**: module separation, process-gated connection lifecycle, retries, config clamping, console/tray patterns. Its current version is Go/Wails. No League-specific logic, identity sources or code were copied.

## Known limitations

- Playlist IDs are **UNVERIFIED**, including the supplied 1/2/3/4/6/10/11/13/27/28/29/30/34 table; official docs do not enumerate them. Unknown values show `Playlist <id>` and log once at INFO.
- Arena names and day/night/snow variants are best effort. Case-insensitive family aliases tolerate suffix variants; unknown arenas use the raw name and `rl_logo`, logging once at INFO. Complete the table from real DEBUG values, then upload any new asset keys.
- Identity and overtime direction need real packet confirmation. A history replay joined after missing ReplayCreated can look like a goal replay because bReplay alone does not distinguish them.
- Automated tests verify mocked Discord IPC boundaries and lifecycle. Real Windows TCP packets also verified encoded Data, Stadium_P and training playlist 9. Your actual Discord Application ID and uploaded art assets are not covered by these tests; other arena/playlist and overtime assumptions still need live confirmation.
- Stats WebSocket is an explicitly configured alternative, not automatic failover. The game API is disabled by default and always requires a full restart after ini changes.

The mock also supports `--encoded-data` to replay the observed real TCP envelope. Katlicia/LOLCustomRPC was consulted only for GUI/worker-thread and save/cancel architecture; no League data logic is used.
