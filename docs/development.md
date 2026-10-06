# Development / Geliştirme

[English overview](../README.md) · [Türkçe](../README.tr.md)

Run all commands from the repository root. The application remains in the
existing `rocket_league_rpc` package; README assets are separate from packaged
desktop assets.

## Setup, test and build

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe run.py
.\.venv\Scripts\python.exe -m pytest
.\build.ps1 -Python .\.venv\Scripts\python.exe
```

The Windows single-file output is `dist/rl-presence.exe`. The build includes
`rocket_league_rpc/ui/`; public `assets/` images are used by GitHub and do not
change the desktop logo or require additional runtime dependencies.

## Module responsibilities

| Area | Files |
| --- | --- |
| Entry and lifecycle | `run.py`, `main.py`, `runtime.py` |
| Settings and install discovery | `config.py`, `installer.py`, `game_watcher.py` |
| Read-only game data | `stats_client.py`, `state.py` |
| Discord formatting and IPC | `presence.py`, `rpc.py`, `ranks.py`, `maps.py`, `modes.py` |
| Desktop bridge and native window | `gui.py`, `window_chrome.py`, `ui/` |
| Languages, reports and updates | `i18n.py`, `reports.py`, `updates.py` |
| Simulation and regression checks | `mock_stats_server.py`, `tests/` |

## Simulated match

Quit Rocket League to free port 49123. Use two terminals:

```powershell
.\.venv\Scripts\python.exe -m rocket_league_rpc.mock_stats_server --port 49123 --delay 5
.\.venv\Scripts\python.exe run.py --mock-game --debug --raw-packets
```

The mock server deliberately fragments/concatenates packets. The automated
end-to-end test uses a real local socket and mocked Discord and does not need
the game or Discord running.

## Repository rules

- Keep user config, logs, update downloads, caches and compiled outputs out of Git.
- Keep README images under `assets/`; keep bundled UI files under `rocket_league_rpc/ui/`.
- Put detailed setup/reference documents in `docs/`; retain third-party license notices.
- Do not add League-specific logic or undocumented private game data sources.
- Update both app version declarations for a release; update both README pages when features change.

## More detail

[Configuration, timestamps and API assumptions](usage.md) ·
[Ayarlar ve API sınırları](usage.tr.md) ·
[Release publishing](releasing.md) ·
[Art asset keys](art-assets.md) ·
[Validation record](qa/verification.md)

## v0.2.7 additions

`identity.py` owns pure normalization/providers/resolution; `identity_probe.py` is read-only development diagnostics. Existing state/runtime/GUI ownership is unchanged. `packaging/windows_launcher.cs` embeds the PyInstaller one-file core; build.ps1 compiles it with the .NET 4.x compiler already required by pywebview. The user receives one EXE. The verified core is cached by SHA-256 under LocalAppData/RL Presence/runtime; config/logs/updates stay beside the user-facing EXE. No arbitrary cache tree cleanup runs.
