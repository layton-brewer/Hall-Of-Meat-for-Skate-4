# ReSkate Hall of Meat

Skate 3's Hall of Meat for skate. through [ReSkate](https://github.com/Dingo-Shenanigans/ReSkate). Crash,
and the picture closes in to a dark, grainy spotlight while your skeleton shows through the body:
every bruised, dislocated and broken bone lit up as it happens, with Skate 3's Thrasher score panel.

## Download

- **[Latest release](https://github.com/layton-brewer/ReSkate-Hall-Of-Meat/releases/latest)** (also on the
  [ReSkate fork](https://github.com/layton-brewer/ReSkate/releases/latest)):
  - `ReSkate-HallOfMeat-<version>.zip`: ReSkateLauncher.exe and ReSkate.dll (official ReSkate v2.0.1 plus
    Skate 3 Hall of Meat, so multiplayer works with everyone on v2.0.1).
  - `Hall_of_Meat-<version>.zip`: the asset pack (Thunderstore format).
- ReSkate 2.0 has its own, separate Hall of Meat (Custom Stuff > Player > Hall of Meat). This one stands
  down whenever that one is switched on, so only one shows at a time.

## Install

1. Close the game.
2. Copy `ReSkateLauncher.exe` and `ReSkate.dll` beside `Skate.exe`.
3. Drag the asset pack zip onto the launcher's MODS page, or extract it into `Mods\Hall_of_Meat\`.
4. Start the game with that launcher (it does not update itself, so it keeps Hall of Meat).

Turn Hall of Meat off by turning the asset pack off in the MODS tab (Insert menu). Console: `hom status`.

## What is in it

- **X-ray** drawn with Skate 3's own 19 bone meshes and bone texture, placed on the ragdoll's physics
  bodies every frame, from the crash until you get up.
- **Skate 3's damage model**, taken from its attribute database: 25 body parts, up to six levels each
  (bruised to broken) with Skate 3's points and impact thresholds, and hits passed to linked parts.
- **Skate 3's score graphs** for bail time, drop, air, speed and rotation (they reproduce the original
  HUD's readings), and the HUD rules from its `homscoring` script.
- **Skate 3's bone-crunch sounds**, decoded from its HOM banks.
- **The HoM look**, measured from Skate 3's footage: cool blue-grey, colour pulled out, black corners,
  coarse film grain.
- **Crash detection** tuned frame by frame on 20 test recordings: wipeouts, slams, being knocked off,
  crash landings onto ramps and on-foot falls start it at once; glides, dives, hippy jumps, plants and
  stepping off do not.

## This repository

| Folder | Contents |
|---|---|
| `mod/` | The Thunderstore asset pack: manifest, README, changelog, icon, and `HallOfMeat/` (Skate 3's art, X-ray meshes, sounds, fonts). |
| `source/` | A snapshot of `Extension/Skate3HallOfMeat/` from the fork (the live code is in [layton-brewer/ReSkate](https://github.com/layton-brewer/ReSkate/tree/skate3-hom-2.0.1)). |
| `tests/` | `core_test.cpp`: offline checks of the crash detection and scoring, many rebuilt from test-video logs. |
| `tools/` | The Skate 3 research tools: XEX decryption, EA APT script disassembly, attribute vault reader and name hashing, EA-XMA sound decoding, texture and mesh export. |
| `docs/` | `HOM-FINDINGS.md`: what Skate 3's files say about Hall of Meat. |

Hall of Meat, its art, meshes and sounds are from Skate 3 by EA Black Box; Thrasher is a trademark of
High Speed Productions. Fan project, not affiliated with or endorsed by EA.
