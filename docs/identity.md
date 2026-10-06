# Automatic account detection / Otomatik hesap algılama — v0.2.7

The official Stats API does **not** identify the local player. `Game.Target` is
the currently viewed car. RL Presence reads local launch/account hints, then
validates them against the current `Players[]` before using personal stats.

## Sources and priority

1. Optional explicit name/PrimaryId in **General → Advanced / Manual override**,
   only when it uniquely matches this lobby.
2. Sanitized RocketLeague.exe Epic launch identity; running Steam's registry
   ActiveUser; otherwise the unique MostRecent user in loginusers.vdf.
3. Low-confidence Target voting: the same player in at least five consecutive
   UpdateStates and at least 80% of the last ten samples. Spectating or any
   previously observed spectator-only player fields disables this fallback
   for the remainder of the match. A view change immediately removes its stats.

PrimaryId comparison uses `(casefold(platform), uid)` and ignores the optional
splitscreen suffix. SteamID64 is `76561197960265728 + ActiveUser`. ID matches
beat candidate-name matches; names use Unicode NFKC, casefold, collapsed
whitespace and an optional leading `[TAG]`. Duplicate names are never guessed.
An explicit platform is a preference, never a filter that hides a unique match.
Stale hints fall through, with one redacted warning per source per match.

Discovery runs at game start and every new match. Match-validated IDs can be
learned atomically when `auto_learn_primary_id` is enabled; low-confidence
Target IDs are never saved. The internal `learned_primary_id` origin marker distinguishes learned cache from user input: a fresh match-validated provider beats learned cache even if the previous account is also in the lobby. Editing PrimaryId in Advanced clears that marker. Saving UI settings never counts as another Target packet. Schema 3 preferences migrate to schema 4 with
`identity_mode: "auto"`, preserving old optional overrides. Manual mode disables
automatic candidates and Target voting. Account/source/confidence appear in
General and diagnostics.json. Unidentified personal lines are omitted rather
than displaying three dashes; partial missing fields of an identified player
remain unknown. No previous account's personal values survive a switch.

## Empirical check on this machine (2026-10-06)

`python run.py --identity-probe` exited successfully, without a network request
or settings/log/INI writes. Steam was running; HKCU ActiveProcess.ActiveUser
was readable. Its converted ID matched the **single** account block in the
readable loginusers.vdf. That file had PersonaName/Timestamp/AccountName but no
MostRecent field, so the verified registry provider is used; the fallback does
not guess an account when MostRecent is absent.

RocketLeague.exe was **not running** and no real UpdateState was available in
the inspected raw packet logs. Consequently this run cannot establish this
user's live `Players[].PrimaryId` shape or compare game name with Steam persona.
`Steam|<id>|0` / Epic parameters are fixture examples, **UNVERIFIED on this
machine**, not empirical claims. Epic launch parameter spelling, elevated game
access and Steam offline-mode behavior remain **UNVERIFIED**. They are guarded,
and every available candidate still requires current-match validation.

## Privacy

Detection is local and read-only: process command line, registry, loginusers.vdf.
Secret-like arguments containing AUTH, PASSWORD, TOKEN, EXCHANGE, SECRET or
CREDENTIAL and their values are discarded at the process-reader boundary.
Only public argument names and allowlisted Epic username/user ID reach the
providers. Authentication values are never parsed, logged, persisted or sent.
The probe redacts IDs. INFO/WARNING identity logs redact identifiers; full
identity IDs are available only at DEBUG. Opt-in raw Stats logs contain player
names/IDs: redact them before sharing. The issue-report body remains exactly
title/description/version/os; account data and diagnostics are not attached.

## Manual acceptance checks

1. **Steam normal:** leave name/ID blank and identity_mode auto, launch Steam's
   game, join a match. General should identify a Steam account with match
   validation; goals/saves/points must match your own row in diagnostics.
2. **Epic launch:** launch Epic's game. Check readable sanitized argument names
   with the probe; expect Epic source only if parameters exist and match a
   current Player PrimaryId. Never share raw launch arguments.
3. **Account switch:** close the game, switch account/launcher, start another
   match. No field clearing is needed; check new identity and no stale stats.
4. **Game started as admin:** run the app normally. AccessDenied must not crash
   it; available Steam identity may still validate. Otherwise the account is
   unidentified or explicitly low-confidence, never presented as certain.
5. **Steam offline mode:** check whether ActiveUser remains readable while Steam
   runs. If unavailable, only a unique MostRecent entry is accepted. If neither
   exists, no platform identity is invented.

The live timer and the existing five-writes-per-20-seconds budget are unchanged.
Normal changes coalesce for at least four seconds; personal-stat changes are
priority updates when the rolling budget allows them.

## Türkçe

Hesap bilgileri yalnızca bu bilgisayarda okunur; mevcut maçın oyuncularıyla
eşleşmeden kullanılmaz. İsim/platform yazmak veya hesap değiştirince PrimaryId
temizlemek gerekmez. Genel'deki hesap satırı kaynak ve güveni gösterir. İsteğe
bağlı elle seçim **Genel → Gelişmiş / Elle kimlik seçimi** altındadır.
Algılanamayan kişisel istatistik satırı Discord'a gönderilmez. Target tahmini
kesin kimlik değildir ve düşük güven olarak işaretlenir.

Bu makinede çalışan Steam'in ActiveUser kaydı, loginusers.vdf'deki tek hesapla
eşleşti. Dosyada MostRecent alanı yoktu. Oyun kapalı ve gerçek UpdateState
günlüğü bulunmadığı için canlı ID biçimi/ad eşleşmesi, Epic parametreleri,
yönetici oyunu ve Steam çevrimdışı modu **UNVERIFIED / doğrulanmadı**.
Yukarıdaki beş kontrolü gerçek Steam/Epic maçlarında tamamlayın. Gizli başlatma
parametreleri kaydedilmez; sorun raporuna hesap veya günlük eklenmez.
