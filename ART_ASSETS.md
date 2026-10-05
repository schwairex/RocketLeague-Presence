# Discord Art Assets — v0.2.3

TR: Sabit Discord uygulaması **802869954805760020** için Rich Presence → Art Assets
alanına aşağıdaki küçük harfli anahtarlarla görsel yükleyin. Son kullanıcıların
görsel yüklemesi gerekmez. Varyantlar temel haritanın görselini, Rocket Labs
haritaları `rocket_labs` görselini paylaşır. Harita adı yine ayrı gösterilir.

EN: Upload these exact lowercase keys to that application's Rich Presence →
Art Assets. End users do not upload images. Variants reuse base artwork;
Rocket Labs layouts share `rocket_labs` while retaining distinct display names.

## New keys / Yeni eklenecek anahtarlar

`arctagon`, `boostfield_mall`, `calavera`, `carbon`, `champions_field`, `core_707`, `deadeye_canyon`, `deadeye_canyon_oasis`, `drift_woods`, `dunk_house`, `estadio_vida`, `futura_garden`, `midnight_metro`, `neon_fields`, `parc_de_paris`, `quadron`, `rivals_arena`, `rocket_labs`, `salty_shores`, `sovereign_heights`, `starbase_arc`, `starbase_arc_aftermath`, `sunset_dunes`, `the_block`, `throwback_stadium`, `united_futura`

## Full list / Tam liste

| Exact key / Birebir anahtar | Artwork / Görsel |
|---|---|
| `aquadome` | Aquadome |
| `arctagon` | Arctagon |
| `beckwith_park` | Beckwith Park |
| `blue` | Blue team icon / Mavi takım |
| `boostfield_mall` | Boostfield Mall |
| `calavera` | Calavera |
| `carbon` | Carbon |
| `champions_field` | Champions Field |
| `core_707` | Core 707 |
| `deadeye_canyon` | Deadeye Canyon |
| `deadeye_canyon_oasis` | Deadeye Canyon (Oasis) |
| `dfh_stadium` | DFH Stadium |
| `drift_woods` | Drift Woods |
| `dunk_house` | Dunk House |
| `estadio_vida` | Estadio Vida |
| `farmstead` | Farmstead |
| `forbidden_temple` | Forbidden Temple |
| `futura_garden` | Futura Garden |
| `mannfield` | Mannfield |
| `midnight_metro` | Midnight Metro |
| `neo_tokyo` | Neo Tokyo |
| `neon_fields` | Neon Fields |
| `orange` | Orange team icon / Turuncu takım |
| `parc_de_paris` | Parc de Paris |
| `quadron` | Quadron |
| `rivals_arena` | Rivals Arena |
| `rl_logo` | Rocket League logo |
| `rocket_labs` | Rocket Labs layouts / Rocket Labs ortak görseli |
| `salty_shores` | Salty Shores |
| `sovereign_heights` | Sovereign Heights |
| `starbase_arc` | Starbase ARC |
| `starbase_arc_aftermath` | Starbase ARC (Aftermath) |
| `sunset_dunes` | Sunset Dunes |
| `the_block` | The Block |
| `throwback_stadium` | Throwback Stadium |
| `united_futura` | United Futura |
| `urban_central` | Urban Central |
| `utopia_coliseum` | Utopia Coliseum |
| `wasteland` | Wasteland |

## Coverage / Kapsam

104 exact Arena names / birebir Arena değeri; 39 unique asset keys / farklı görsel anahtarı.

TR: `Paname_Dusk_P` → Parc de Paris → `parc_de_paris`. Harf duyarsız arama
ve en uzun eşleşen aileyle varyant desteği vardır. Gelecekteki/bilinmeyen
değerler ham ad ve `rl_logo` ile gösterilir; INFO loguna bir kez yazılır.
Tablo bütün bilinen mevcut standart, özel mod, Rocket Labs ve Knockout
eşleştirmelerini kapsayacak şekilde genişletildi; resmî Stats API eksiksiz bir
Arena listesi yayımlamadığı için mutlak/tüm gelecek harita kapsamı garanti edilmez.
`UF_Night_P` → United Futura eşleştirmesi kurulu oyun paketinden ve Season 23
haberinden çıkarımdır; gerçek API paketleriyle doğrulanmalıdır.

EN: `Paname_Dusk_P` maps to Parc de Paris (`parc_de_paris`). Lookup ignores case
and supports variants via the longest known family. Unknown/future arenas
retain their raw name with `rl_logo` and log once. The official API provides no
exhaustive Arena catalog, so this remains a best-effort table, including special
mode, Rocket Labs and Knockout arenas. `UF_Night_P` → United Futura is inferred
from the installed package and Season 23 news; verify with real packets.

Mapping references / Eşleştirme kaynakları:
[RLBot's maintained arena table](https://github.com/RLBot/python-interface/blob/master/rlbot/utils/maps.py),
[Official Season 21 notes](https://www.rocketleague.com/news/rocket-league-patch-notes-v2-63-season-21-live),
[Official Season 23 arena news](https://www.rocketleague.com/news/hit-the-pitch-for-the-world-cup-in-rocket-league-season-23/).
These supply name facts only; runtime data comes solely from the official Stats API.

## Arena table / Arena tablosu

| Arena | Display name / Görünen ad | Asset key |
|---|---|---|
| `ARC_Darc_P` | Starbase ARC (Aftermath) | `starbase_arc_aftermath` |
| `ARC_P` | Arctagon | `arctagon` |
| `ARC_Standard_P` | Starbase ARC | `starbase_arc` |
| `BB_P` | Champions Field (NFL) | `champions_field` |
| `Beach_Night_GRS_P` | Salty Shores (Salty Fest) | `salty_shores` |
| `Beach_Night_P` | Salty Shores (Night) | `salty_shores` |
| `Beach_P` | Salty Shores | `salty_shores` |
| `CHN_Stadium_Day_P` | Forbidden Temple (Day) | `forbidden_temple` |
| `CHN_Stadium_P` | Forbidden Temple | `forbidden_temple` |
| `CS_Day_P` | Champions Field (Day) | `champions_field` |
| `CS_HW_P` | Rivals Arena | `rivals_arena` |
| `CS_P` | Champions Field | `champions_field` |
| `EuroStadium_Dusk_P` | Mannfield (Dusk) | `mannfield` |
| `EuroStadium_Night_P` | Mannfield (Night) | `mannfield` |
| `EuroStadium_P` | Mannfield | `mannfield` |
| `EuroStadium_Rainy_P` | Mannfield (Stormy) | `mannfield` |
| `EuroStadium_Snow_P` | Mannfield (Snowy) | `mannfield` |
| `EuroStadium_SnowNight_P` | Mannfield (Snowy) | `mannfield` |
| `Farm_GRS_P` | Farmstead (Pitched) | `farmstead` |
| `Farm_HW_P` | Farmstead (Spooky) | `farmstead` |
| `Farm_Night_P` | Farmstead (Night) | `farmstead` |
| `Farm_P` | Farmstead | `farmstead` |
| `FF_Dusk_P` | Estadio Vida (Dusk) | `estadio_vida` |
| `FNI_Stadium_P` | Forbidden Temple (Fire and Ice) | `forbidden_temple` |
| `Haunted_TrainStation_P` | Urban Central (Haunted) | `urban_central` |
| `HoopsStadium_P` | Dunk House | `dunk_house` |
| `HoopsStreet_Art_P` | The Block | `the_block` |
| `HoopsStreet_P` | The Block | `the_block` |
| `KO_Calavera_P` | Calavera | `calavera` |
| `KO_Carbon_P` | Carbon | `carbon` |
| `KO_Quadron_P` | Quadron | `quadron` |
| `Labs_4v4_Arena15_Blackout_P` | Midnight Metro (Quads) | `midnight_metro` |
| `Labs_4v4_Arena15_EuroStadium_Night_P` | Mannfield (Quads) | `mannfield` |
| `Labs_4v4_Arena15_Retro_P` | Sunset Dunes (Quads) | `sunset_dunes` |
| `Labs_Basin_P` | Basin | `rocket_labs` |
| `Labs_CirclePillars_P` | Pillars | `rocket_labs` |
| `Labs_Corridor_P` | Corridor | `rocket_labs` |
| `Labs_Cosmic_P` | Cosmic | `rocket_labs` |
| `Labs_Cosmic_V4_P` | Cosmic | `rocket_labs` |
| `Labs_DoubleGoal_P` | Double Goal | `rocket_labs` |
| `Labs_DoubleGoal_V2_P` | Double Goal | `rocket_labs` |
| `Labs_Galleon_Mast_P` | Galleon (Retro) | `rocket_labs` |
| `Labs_Galleon_P` | Galleon | `rocket_labs` |
| `Labs_Holyfield_P` | Loophole | `rocket_labs` |
| `Labs_Holyfield_Space_P` | Holyfield | `rocket_labs` |
| `Labs_Octagon_02_P` | Octagon | `rocket_labs` |
| `Labs_Octagon_B2B_02_P` | Roadblock | `rocket_labs` |
| `Labs_Octagon_P` | Octagon | `rocket_labs` |
| `Labs_Octagon_Vent_P` | Octagon (Vent) | `rocket_labs` |
| `Labs_PillarGlass_P` | Hourglass | `rocket_labs` |
| `Labs_PillarHeat_P` | Barricade | `rocket_labs` |
| `Labs_PillarWings_P` | Colossus | `rocket_labs` |
| `Labs_Underpass_P` | Underpass | `rocket_labs` |
| `Labs_Underpass_v0_P` | Underpass | `rocket_labs` |
| `Labs_Utopia_P` | Utopia Retro | `rocket_labs` |
| `Mall_Day_P` | Boostfield Mall | `boostfield_mall` |
| `Music_P` | Neon Fields | `neon_fields` |
| `NeoTokyo_Arcade_P` | Neo Tokyo (Arcade) | `neo_tokyo` |
| `NeoTokyo_Hax_P` | Neo Tokyo (Hacked) | `neo_tokyo` |
| `NeoTokyo_Hax_Signs_Off_P` | Neo Tokyo (Hacked) | `neo_tokyo` |
| `NeoTokyo_Hax_Signs_P` | Neo Tokyo (Hacked) | `neo_tokyo` |
| `NeoTokyo_P` | Neo Tokyo | `neo_tokyo` |
| `NeoTokyo_Standard_P` | Neo Tokyo | `neo_tokyo` |
| `NeoTokyo_Toon_P` | Neo Tokyo (Comic) | `neo_tokyo` |
| `Outlaw_Oasis_P` | Deadeye Canyon (Oasis) | `deadeye_canyon_oasis` |
| `Outlaw_P` | Deadeye Canyon | `deadeye_canyon` |
| `Paname_Dusk_P` | Parc de Paris | `parc_de_paris` |
| `Park_Bman_P` | Beckwith Park (Gotham Night) | `beckwith_park` |
| `Park_Night_P` | Beckwith Park (Midnight) | `beckwith_park` |
| `Park_P` | Beckwith Park | `beckwith_park` |
| `Park_Rainy_P` | Beckwith Park (Stormy) | `beckwith_park` |
| `Park_Snowy_P` | Beckwith Park (Snowy) | `beckwith_park` |
| `ShatterShot_P` | Core 707 | `core_707` |
| `Stadium_10A_P` | DFH Stadium (Anniversary) | `dfh_stadium` |
| `Stadium_Day_P` | DFH Stadium (Day) | `dfh_stadium` |
| `Stadium_Foggy_P` | DFH Stadium (Stormy) | `dfh_stadium` |
| `Stadium_P` | DFH Stadium | `dfh_stadium` |
| `Stadium_Race_Day_P` | DFH Stadium (Circuit) | `dfh_stadium` |
| `Stadium_Winter_P` | DFH Stadium (Snowy) | `dfh_stadium` |
| `Street_P` | Sovereign Heights | `sovereign_heights` |
| `Swoosh_P` | Champions Field (Nike FC) | `champions_field` |
| `ThrowbackHockey_P` | Throwback Stadium (Snowy) | `throwback_stadium` |
| `ThrowbackStadium_P` | Throwback Stadium | `throwback_stadium` |
| `TrainStation_Dawn_P` | Urban Central (Dawn) | `urban_central` |
| `TrainStation_Night_P` | Urban Central (Night) | `urban_central` |
| `TrainStation_P` | Urban Central | `urban_central` |
| `UF_Day_P` | Futura Garden | `futura_garden` |
| `UF_Night_P` | United Futura | `united_futura` |
| `Underwater_GRS_P` | Aquadome (Shallows) | `aquadome` |
| `Underwater_P` | Aquadome | `aquadome` |
| `Utopia_Stadium` | Utopia Coliseum | `utopia_coliseum` |
| `UtopiaStadium_Dusk_P` | Utopia Coliseum (Dusk) | `utopia_coliseum` |
| `UtopiaStadium_Lux_P` | Utopia Coliseum (Gilded) | `utopia_coliseum` |
| `UtopiaStadium_P` | Utopia Coliseum | `utopia_coliseum` |
| `UtopiaStadium_Snow_P` | Utopia Coliseum (Snowy) | `utopia_coliseum` |
| `Wasteland_Art_P` | Wasteland | `wasteland` |
| `Wasteland_GRS_P` | Wasteland (Pitched) | `wasteland` |
| `Wasteland_Night_P` | Wasteland (Night) | `wasteland` |
| `Wasteland_Night_S_P` | Wasteland (Night) | `wasteland` |
| `Wasteland_P` | Wasteland | `wasteland` |
| `Wasteland_S_P` | Wasteland | `wasteland` |
| `Woods_Forest_P` | Drift Woods (Forest) | `drift_woods` |
| `Woods_Night_P` | Drift Woods (Night) | `drift_woods` |
| `Woods_P` | Drift Woods | `drift_woods` |
