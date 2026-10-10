// Local tool (not shipped): runs the launch merge on a sandbox data root and prints the report.
//   ogcam_merge_check <sandboxRoot>   (sandboxRoot/Data -> the game's Data, sandboxRoot/Mods holds the mods)
#include "Engine/Vfs/mod_catalog.h"

#include <iostream>

int main(int argc, char** argv) {
    if (argc < 2) return 2;
    const auto catalog = dingosdk::mods::load_catalog(argv[1]);
    std::cout << "issue: " << catalog.issue << "\nmerged: " << catalog.merged << "\n";
    for (const auto& note : catalog.notes) std::cout << "note: " << note << "\n";
    for (const auto& warning : catalog.warnings) std::cout << "warning: " << warning << "\n";
    for (const auto& mod : catalog.mods) std::cout << "mod: " << dingosdk::mods::describe(mod) << "\n";
    for (const auto& mod : catalog.excluded) std::cout << "excluded: " << mod.name << "\n";
    for (const auto& mod : catalog.outdated) std::cout << "outdated: " << mod.name << " " << mod.outdated << "\n";
    return catalog.merged ? 0 : 1;
}
