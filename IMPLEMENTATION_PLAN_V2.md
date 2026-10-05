# v0.2.0 — native HTML interface and explicit telemetry

User intent: replace the console window with the supplied 1120×760 Turkish HTML design, make connection failures visible, show all requested live match/player stats, and show rank/division plus detailed activities.

User decision: use only the official Rocket League Stats API. Rank/division and states that API does not expose (shop, queue, main menu, training) are selected manually. No BakkesMod, League data access, private API, telemetry service or game commands.

Evidence: local install is D:\SteamLibrary\steamapps\common\rocketleague; DefaultStatsAPI.ini already contains PacketSendRate=30/Port=49123/WebPort=49124. The game process is running. A localhost TCP connection succeeds but a three-second read produces no events. That is a connected/awaiting-data condition, not evidence of a live match or of a broken parser. The old app hides this distinction behind a generic menu presence.

Architecture: keep the tested asyncio core; add a pywebview Windows window on the main thread with the original HTML/CSS/vector assets and offline font files. Run the engine on its own thread. The bridge schedules all engine mutations onto that thread and exposes snapshots, preview, validated save/cancel, install repair, diagnostics and window actions. Live official match packets override manual menu activities. Empty/missing local-player stats remain unknown.

Reference: Katlicia/LOLCustomRPC reviewed only for UI/backend separation and draft-preview/save/cancel configuration flow. Its League data sources and analytics are excluded.

1. [ ] Tests first: missing player statistics, manual rank/activity, stopped timer toggle, auto training playlist, independent connection/last-event diagnostics, hot config reload and GUI background-thread shutdown.
2. [ ] Implement core/config/diagnostics fixes; retain every existing parser/reducer/RPC limit regression.
3. [ ] Extract the user-supplied visual assets as data, discard its runtime scripts, build functional native GUI bridge and exact main-view DOM. Add General fields for Application ID, installation, player ID, manual rank/division/activity and connection repair.
4. [ ] Verify primary interactions and same-viewport visual fidelity against the supplied HTML, recording screenshot comparisons in design-qa.md.
5. [ ] Run complete pytest and TCP end-to-end tests, build the no-console Windows exe, smoke-test the actual GUI, update bilingual documentation and package versioned downloads.

Constraints: 15-second Discord activity floor remains mandatory; app UI can update every 0.5 seconds. GUI preview samples never publish fake match stats. Save applies without restart; cancel restores the persisted draft. Live telemetry and the actual last sent Discord payload are distinguishable. Do not quit/restart the user's running game automatically.
