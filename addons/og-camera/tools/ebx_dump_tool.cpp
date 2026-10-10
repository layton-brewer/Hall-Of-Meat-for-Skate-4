// Local research tool (not shipped): lists every EBX asset in the game's data and dumps matches.
//   ebx_dump list <gameRoot>                 -> "toc | bundle | asset" per line
//   ebx_dump dump <gameRoot> <substr> [max]  -> decoded field tree of each asset whose name contains substr
//   ebx_dump type <gameRoot> <substr> <rootTypeSubstr>  -> asset names whose root type matches
#include "Engine/Vfs/mod_merge_internal.h"
#include "Engine/Resource/ebx_document.h"
#include "Engine/Resource/cas_codec.h"

#include <iostream>
#include <sstream>

using namespace dingosdk::mods::detail;
namespace ebx = dingosdk::frostbite::ebx;

namespace {
void print_value(const ebx::Document& doc, const ebx::Value& v, int depth, std::ostream& out);

void print_object(const ebx::Document& doc, const ebx::Object& o, int depth, std::ostream& out) {
    const std::string pad(depth * 2, ' ');
    if (o.descriptor >= 0 && o.descriptor < (int)doc.types.size()) out << "<" << doc.types[o.descriptor].name << ">";
    out << "\n";
    for (const auto& f : o.fields) {
        out << pad << f.name << " = ";
        print_value(doc, f.value, depth + 1, out);
    }
}

void print_value(const ebx::Document& doc, const ebx::Value& v, int depth, std::ostream& out) {
    std::visit([&](const auto& d) {
        using T = std::decay_t<decltype(d)>;
        if constexpr (std::is_same_v<T, std::monostate>) out << "-\n";
        else if constexpr (std::is_same_v<T, bool>) out << (d ? "true" : "false") << "\n";
        else if constexpr (std::is_same_v<T, std::int64_t> || std::is_same_v<T, std::uint64_t> || std::is_same_v<T, double>) out << d << "\n";
        else if constexpr (std::is_same_v<T, std::string>) out << '"' << d << "\"\n";
        else if constexpr (std::is_same_v<T, dingosdk::frostbite::Guid>) out << d.string() << "\n";
        else if constexpr (std::is_same_v<T, ebx::PointerReference>) {
            if (d.kind == ebx::PointerKind::null) out << "null\n";
            else if (d.kind == ebx::PointerKind::internal) {
                out << "-> #" << d.index;
                if (d.index >= 0 && d.index < (int)doc.instances.size()) {
                    const auto& inst = doc.instances[d.index];
                    if (inst.object && inst.object->descriptor >= 0) out << " " << doc.types[inst.object->descriptor].name;
                }
                out << "\n";
            } else {
                out << "-> import #" << d.index;
                if (d.index >= 0 && d.index < (int)doc.imports.size()) out << " " << doc.imports[d.index].fileGuid.string();
                out << "\n";
            }
        }
        else if constexpr (std::is_same_v<T, std::shared_ptr<ebx::Object>>) { if (d) print_object(doc, *d, depth, out); else out << "{}\n"; }
        else if constexpr (std::is_same_v<T, ebx::Value::Array>) {
            out << "[" << d.size() << "]\n";
            const std::string pad(depth * 2, ' ');
            for (std::size_t i = 0; i < d.size() && i < 256; ++i) { out << pad << "[" << i << "] "; print_value(doc, d[i], depth + 1, out); }
        }
        else out << "?\n";
    }, v.data);
}
}

int main(int argc, char** argv) {
    if (argc < 3) { std::cerr << "usage\n"; return 2; }
    const std::string mode = argv[1];
    const fs::path game = argv[2];
    const fs::path data = game / "Data";
    const std::string needle = argc > 3 ? lower(argv[3]) : "";
    const std::string typeNeedle = argc > 4 ? lower(argv[4]) : "";
    const std::size_t maxDump = (mode == "dump" && argc > 4) ? std::stoul(argv[4]) : 50;
    auto layout = dingosdk::vfs::read_layout(data / "layout.toc");
    CasStore store(data, game / "nul_out", layout.root);
    std::size_t dumped = 0;
    for (const auto& entry : fs::recursive_directory_iterator(data / "Win32")) {
        if (!entry.is_regular_file() || entry.path().extension() != ".toc") continue;
        fb::TocDocument toc;
        try { toc = fb::read_toc(read_file(entry.path())); } catch (const std::exception& e) {
            std::cerr << "toc fail " << entry.path().string() << ": " << e.what() << "\n"; continue; }
        const auto rel = fs::relative(entry.path(), data).generic_string();
        for (const auto& bundle : toc.bundles) {
            std::optional<Listing> listing;
            try { listing = list_bundle(store, data, data, bundle, game); } catch (...) {}
            if (!listing) continue;
            for (std::size_t i = 0; i < listing->manifest.ebx.size(); ++i) {
                const auto name = lower(listing->manifest.ebx[i].name);
                if (mode == "list") { std::cout << rel << " | " << bundle.name << " | " << name << "\n"; continue; }
                if (!needle.empty() && name.find(needle) == std::string::npos) continue;
                try {
                    auto doc = ebx::read_document(read_asset(store, data, data, *listing, i, game));
                    if (mode == "guids") { std::cout << doc.fileGuid.string() << " " << name << " " << doc.rootType << "\n"; continue; }
                    if (mode == "type") {
                        if (lower(doc.rootType).find(typeNeedle) != std::string::npos)
                            std::cout << doc.rootType << " | " << name << " | " << bundle.name << "\n";
                        continue;
                    }
                    std::cout << "===== " << name << " (" << doc.rootType << ") in " << bundle.name << "\n";
                    for (std::size_t k = 0; k < doc.instances.size(); ++k) {
                        const auto& inst = doc.instances[k];
                        if (!inst.object) continue;
                        std::cout << "#" << k << " " << inst.instanceGuid.string() << " ";
                        print_object(doc, *inst.object, 1, std::cout);
                    }
                    if (++dumped >= maxDump) return 0;
                } catch (const std::exception& e) { std::cerr << "fail " << name << ": " << e.what() << "\n"; }
            }
        }
    }
    return 0;
}
