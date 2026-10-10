# Hall of Meat for Skate 4

**The nostalgic one.** Skate 3's Hall of Meat, back in skate. through ReSkate, rebuilt from Skate 3's
own files. Crash, and the picture closes in to a dark, grainy blue-grey spotlight while your skeleton
shows through the body: hurt bones glow orange, breaks burn red and the game drops into slow motion,
while Skate 3's Thrasher score panel counts your bail the way Skate 3 did.

## What's in it
- **X-ray skeleton** drawn with Skate 3's own bone meshes and bone texture, on the ragdoll from the
  moment you crash until you get back up.
- **Skate 3's orange glow**: bones heat from white to orange as they're hurt; breaks burn red-orange.
- **Skate 3's damage model**: 25 body parts, each with up to six damage levels from bruised to
  broken, with Skate 3's points and impact thresholds, and hits that spread to connected parts.
- **Skate 3's score graphs** for bail time, drop, air, speed and rotation, and its HUD rules for
  when each row appears.
- **Skate 3's car bonus**: 2,000 for every car that takes you out, with its own chip.
- **Broken-bone slow motion** with Skate 3's slow-motion sound, and red screen edges on a break
  (single player only; never in multiplayer).
- **Skate 3's bone-crunch sounds**, one for every new injury.
- **The HoM look**: Skate 3's colour matrix on the game picture, spotlight, black corners and film grain.
- **Each map's best bail**, saved with your profile (NEW BEST / BEST under the score).
- Triggers on every crash, on or off the board. Glides, hippy jumps and plants don't count.
- Works in multiplayer sessions (the slow motion stays single player).

## Requirements
- **A ReSkate with Skate 3 Hall of Meat built in.** This package holds Skate 3's art, meshes and
  sounds; the code that draws them is part of ReSkate itself. It is on its way into official ReSkate
  (https://github.com/Dingo-Shenanigans/ReSkate/pull/150): once your ReSkate has it, installing this
  package is all you need. To check, type `hom status` in the console (`~`); if ReSkate doesn't know
  the command, your ReSkate doesn't have it yet.
- **Until then**, use the ReSkate build that has it: get `ReSkate-HallOfMeat-<version>.zip` from
  https://github.com/layton-brewer/Hall-Of-Meat-for-Skate-4/releases/latest and copy
  `ReSkateLauncher.exe` and `ReSkate.dll` beside `Skate.exe`. It is official ReSkate v2.0.1 plus Hall
  of Meat, so multiplayer works with everyone on 2.0.1.
- ReSkate 2.0 has its own, separate Hall of Meat (Custom Stuff > Player > Hall of Meat). Leave that
  one off to see this one; this one steps aside whenever it is on.

## Install
1. Close the game.
2. **ReSkate with Skate 3 Hall of Meat** (skip once official ReSkate ships it, see Requirements):
   download `ReSkate-HallOfMeat-<version>.zip` from
   https://github.com/layton-brewer/Hall-Of-Meat-for-Skate-4/releases/latest, and copy
   `ReSkateLauncher.exe` and `ReSkate.dll` from it into your skate. folder (where `Skate.exe` is),
   replacing the ones there. Steam: right-click skate. > Manage > Browse local files.
3. **This package**: in the ReSkate launcher, open **MODS**, find **Hall of Meat** and install it
   (or drag this zip onto the MODS page). Make sure it is switched on.
4. Start the game with `ReSkateLauncher.exe`. In game, keep ReSkate's own Hall of Meat off
   (Custom Stuff > Player > Hall of Meat).
5. Bail. Hard.

To switch it off, turn the package off in the MODS tab (in game: Insert > MODS).

## Console (`~`)
- `hom status`: shows it is running, and your best bail.
- `hom lead <ms>`: pulls the X-ray ahead if the bones ever trail the body on your machine (saved).

## Troubleshooting
- **Nothing on a crash:** type `hom status`. Unknown command: your ReSkate has no Skate 3 Hall of
  Meat yet (step 2). If it answers, check this package is installed and switched on (step 3), and
  that ReSkate's own Hall of Meat is off (step 4).
- **No bone sounds:** the game found no sound output device; plug one in and they start on their own.
- **It went back to normal after a ReSkate update:** the official launcher puts back the official
  ReSkate.dll. Redo step 2 until official ReSkate includes it.

## Credits
Hall of Meat, its art, meshes and sounds are from Skate 3 by EA Black Box. Thrasher is a trademark of
High Speed Productions. This is a fan project and is not affiliated with or endorsed by EA.
