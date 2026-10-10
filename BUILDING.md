# Building

Everything here is current for **ReSkate v2.0.2** (multiplayer protocol 46), Hall of Meat 1.5.12 and
OG Camera 1.3.0.

## Hall of Meat (the DLL and launcher)

Two ways to get the same code:

1. **The fork:** `git clone -b skate3-hom-2.0.2 https://github.com/layton-brewer/ReSkate-Hall-Of-Meat`
2. **A clean ReSkate:** check out `v2.0.2` of https://github.com/Dingo-Shenanigans/ReSkate and run
   `git apply patches/skate3-hom-on-reskate-2.0.2.patch` from this repository.

Then build it the way ReSkate does (Visual Studio 2026 and CMake, Windows):

```
cmake --preset vs2026
cmake --build build/vs2026 --config Release --target dingosdk_runtime dingosdk_launcher dingosdk_server -j 8
```

The output is `build/vs2026/Release/ReSkate.dll` and `ReSkateLauncher.exe`. The release zip is those two
files, `INSTALL.txt`, and the asset pack from `mod/` as `Mods/Hall_of_Meat/`.

Official ReSkate changes its multiplayer protocol between releases. A build only sees servers on its own
protocol, so rebase onto the newest official release whenever one comes out.

## Tests

`tests/core_test.cpp` checks the crash detection and scoring offline (no game needed):

```
cl /O2 /std:c++20 /EHsc /I <ReSkate checkout> tests\core_test.cpp <ReSkate checkout>\Extension\Skate3HallOfMeat\hom_core.cpp /Fe:core_test.exe
core_test.exe
```

It ends with `0 failure(s)`.

## OG Camera

It is data only. `addons/og-camera/tools/` holds the tools that build it: they read the game's EBX assets
with ReSkate's own libraries and write the changed copies as a mod. See `addons/og-camera/FINDINGS.md` for
how it works and `addons/og-camera/edits.txt` for every value it changes.
