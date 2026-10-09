# Skate 3 Hall Of Meat: what the game files say

Source: `Skate 3 Personal` (Xbox 360 Games-on-Demand) joined with `D:\dev\tools\god2iso.py`, extracted with XBLA-Extract, EB `.big` archives unpacked with `D:\dev\tools\ebbig.py`. Extracted data lives in `D:\dev\skate3-ref\ex` (not for the repo: EA's assets).

## Modes
- `Challenge.eChallengeTypes.HallOfMeatBattle`: turn-based, 1+ players, rounds, random start player, per-turn main timer, `CumulativeScoring` option, leaderboard (rank, name, points), highlight reel and "players choice" vote online.
- `hall_of_meat_sp`: single-player objective version, `hom_*` challenges per district (`hom_dwtn_01..`, `hom_indu_*`, `hom_univ_*`, `ol_hom_*` online spots, DLC `ol_hom_dyr_01`).
- Locators: `*_challengelocator_01` with six `spawnlocator_*`, a `ScoringBoundary` volume. `InScoringBoundary` is set when the skater enters/leaves it; only bails started inside the boundary score.
- Flow states: setup, countdown (your turn), challenge_running, end_turn, highlight_reel, leaderboard, complete.
- Turn logic (Lua, `db/challenge_stategraph/hall_of_meat.bin`): on wipeout (not a physics teleport) the main timer is removed and `IsWipedOut=true`; `wipeoutalmostover` and `wipeoutover` end the turn; `bonesbroken` message exists. `BonePoints = {1, 2, 4}`. HUD components shown: `HOMScoringHUD`, `TimerHUD`, `CountdownHUD`, `DPOHUD` (score title `ID_COMMON_SCORE`), `LeaderboardHUD`; trick display and minimap hidden; `HOM.EnableHOMVisuals(false)` before start.

## Scoring HUD (`fe/source/screens/hud2/homscoring.apt`)
- Metrics (each with an active flag, item index and threshold): **air time**, **bail duration**, **bail speed** (`ID_HOM_SPEED_VALUE`), **body rotation**, **drop distance** (meters). `UpdateMetricsScoring`.
- Bonuses (count + score each): **car**, **dmo** (dynamic map objects), **ped**, **skater**, **body tweak**. `HOM_GetBonusData / GetBonusScores / GetBonusCollisionScore`, `HOM_GetScore`.
- Panel with `mThrasher_bg` (Thrasher-branded), `scoreText`, `statText` with glow, labels, icons; states intro / normal / outro; sounds `FE_SOUND_HOM_SCORE_RED`, `FE_SOUND_HOM_TRANSITION`.
- Textures (21, DXT5, Xbox 360, linear with a padded pitch): panels, Thrasher logo, timer, drop arrow, pins (objects), ped icon, glow. Decoded by `D:\dev\tools\rx2tex.py` into `D:\dev\skate3-ref\tex\homscoring`.

## X-ray skeleton
`content/marquee.big`: `dem_bones_hom` recipe plus 20 bone meshes: Skull, Neck, Rib_Cage, Lower_Spine, Hips, Bicep L/R, Forearm L/R, Hand L/R, Thigh L/R, Calf L/R, Ankle L/R, Toes L/R.

## Audio
`audio/audiofiles.big`: `HOM_Set_1..5.bnk`, `hom_slo_mo.abk`; `livingworldspeech.big`: 24 announcer lines `340_*_HOM.dat`.

## Not recoverable from files
The native point formulas (bone values, metric thresholds) live in `Skate.xex` (PowerPC) and the HUD logic in ActionScript bytecode inside the `.apt`.

## 2026-10-09: settings database, executable, sounds (tools in D:\dev\tools)
- **Attrib vaults** (`db/*.vlt` + `.bin`, big-endian): names are 64-bit Jenkins lookup8 hashes with a=b=0xABCDEF0011223344, c=0x9E3779B97F4A7C13 (`attrib.py`). Collections: key, class, parent, reserve, ?, count, ntypes, typesLen, layout ptr, types[], entries {u64 field, u32 value, u16 type, u16 flags (0x4000 inline)}. Pointers via PtrN {u32 at, u16 type, u16 flag, u64 dest into .bin}. Dumper: `vault.py <vlt> <schema dir> <class> [collections]`.
- **Score graphs** (HoM scoring class layout, bin 0xebbd8+): rotation 720°→750 … 3500°→15000; air 1.5 s→750 … 3.1 s→10000; drop 7 m→750 … 40 m→10000; bail time 5 s→750, 6 s→5000, 8 s→10000, 9 s→15000; speed 10 m/s→750, 12.5→2500, 17.5→5000, 20→10000. Match the video exactly.
- **Body damage**: 25 parts, each 4 links {part, share} + 6 level slots {points, impact}: e.g. hand 100/6 … 1000/18, skull 500/7, 1000/14, 5000/21, groin 1000/3 … 10000/14. Table in hom_core.cpp.
- **post_fx**: colour_matrix_hall_of_meat near/far saturation 0.5, multiply (1,1,1.2); hom_slomo_effect tint (0.4,0.2,0.2); functions_hall_of_meat graphs over score 0..20000.
- **HUD script** (homscoring.apt, `aptdis.py`): row appears when its points > threshold (air 5, others 1) or the game flags it; bonus count shows only from 2.
- **default.xex**: AES (retail key) + LZX; `xexdump.py` decrypts with BCrypt and expands via a CAB with expand.exe -> skate_image.bin. Strings: IsBrokenBoneSlowMo, HOM_GetBodyDamageArray, ID_HOM_BRUISED/SCRAPED/SPRAINED/DISLOCATED/BREAK.
- **Audio**: banks are SPLC with EA SNR/SNS EA-XMA sounds; `eaxma.py` rebuilds XMA2 WAV and decodes with PyAV -> D:\dev\skate3-ref\snd (297 sounds + 4 slow-mo).
