// Local tool (not shipped): builds a data-only ReSkate mod that changes values in the game's EBX assets.
//   ogcam_build <gameRoot> <edits.txt> <outModDir>
// edits.txt:
//   superbundle Win32/levels/game/bam_levelroot/bam_levelroot.toc
//   bundle win32/levels/game/bam_levelroot/bam_levelroot
//   asset <asset name>
//   set <instance guid> <field.path[2].Sub> <number|true|false|null>
#include "Engine/Vfs/mod_merge_internal.h"
#include "Engine/Resource/ebx_document.h"
#include "Engine/Resource/ebx_writer.h"
#include "Engine/Resource/cas_codec.h"

#include <fstream>
#include <iostream>
#include <sstream>

using namespace dingosdk::mods::detail;
namespace ebx = dingosdk::frostbite::ebx;

namespace {
struct Set { std::string verb, guid, path, value; };
struct AssetEdit { std::string name; std::vector<Set> sets; };

ebx::Value* field(ebx::Object& object, const std::string& name) {
    for (auto& f : object.fields) if (lower(f.name) == lower(name)) return &f.value;
    return nullptr;
}

ebx::Value& navigate(ebx::Object& root, const std::string& path) {
    ebx::Object* object = &root;
    ebx::Value* value = nullptr;
    std::stringstream parts(path);
    std::string part;
    while (std::getline(parts, part, '.')) {
        if (!object) throw std::runtime_error("path " + path + ": " + part + " is not inside an object");
        std::string name = part;
        std::vector<std::size_t> indices;
        if (const auto at = part.find('['); at != std::string::npos) {
            name = part.substr(0, at);
            for (auto rest = part.substr(at); !rest.empty();) {
                const auto close = rest.find(']');
                indices.push_back(std::stoul(rest.substr(1, close - 1)));
                rest = rest.substr(close + 1);
            }
        }
        value = field(*object, name);
        if (!value) throw std::runtime_error("path " + path + ": no field " + name);
        for (const auto index : indices) {
            auto* array = std::get_if<ebx::Value::Array>(&value->data);
            if (!array || index >= array->size()) throw std::runtime_error("path " + path + ": bad index");
            value = &(*array)[index];
        }
        auto* nested = std::get_if<std::shared_ptr<ebx::Object>>(&value->data);
        object = nested && *nested ? nested->get() : nullptr;
    }
    return *value;
}

std::string describe(const ebx::Value& value) {
    return std::visit([](const auto& d) -> std::string {
        using T = std::decay_t<decltype(d)>;
        if constexpr (std::is_same_v<T, bool>) return d ? "true" : "false";
        else if constexpr (std::is_same_v<T, double> || std::is_same_v<T, std::int64_t> || std::is_same_v<T, std::uint64_t>) {
            std::ostringstream out; out << d; return out.str();
        }
        else if constexpr (std::is_same_v<T, ebx::PointerReference>)
            return d.kind == ebx::PointerKind::null ? "null" : d.kind == ebx::PointerKind::internal ? "internal#" + std::to_string(d.index)
                                                                                                : "import#" + std::to_string(d.index);
        else return "?";
    }, value.data);
}

void assign(ebx::Value& value, const std::string& text) {
    if (auto* p = std::get_if<ebx::PointerReference>(&value.data)) {
        if (text != "null") throw std::runtime_error("a reference can only be set to null");
        *p = {};
        p->kind = ebx::PointerKind::null;
        p->index = -1;
    } else if (auto* b = std::get_if<bool>(&value.data)) {
        if (text != "true" && text != "false") throw std::runtime_error("a bool takes true or false");
        *b = text == "true";
    } else if (auto* d = std::get_if<double>(&value.data)) *d = std::stod(text);
    else if (auto* i = std::get_if<std::int64_t>(&value.data)) *i = std::stoll(text);
    else if (auto* u = std::get_if<std::uint64_t>(&value.data)) *u = std::stoull(text);
    else throw std::runtime_error("value kind not supported");
}

void text(const ebx::Value& v, std::ostream& out);
void text(const ebx::Object& o, std::ostream& out) {
    out << "{" << o.descriptor;
    for (const auto& f : o.fields) { out << " " << f.name << "="; text(f.value, out); }
    out << "}";
}
void text(const ebx::Value& v, std::ostream& out) {
    std::visit([&](const auto& d) {
        using T = std::decay_t<decltype(d)>;
        if constexpr (std::is_same_v<T, std::shared_ptr<ebx::Object>>) { if (d) text(*d, out); else out << "{}"; }
        else if constexpr (std::is_same_v<T, ebx::Value::Array>) { out << "["; for (const auto& e : d) { text(e, out); out << ","; } out << "]"; }
        else if constexpr (std::is_same_v<T, std::string>) out << '"' << d << '"';
        else if constexpr (std::is_same_v<T, dingosdk::frostbite::Guid>) out << d.string();
        else if constexpr (std::is_same_v<T, ebx::PointerReference> || std::is_same_v<T, bool> || std::is_same_v<T, double> ||
                           std::is_same_v<T, std::int64_t> || std::is_same_v<T, std::uint64_t>) out << describe(v);
        else out << "?";
    }, v.data);
}
std::string text(const ebx::Document& doc) {
    std::ostringstream out;
    out << doc.rootType << " imports " << doc.imports.size() << '\n';
    for (const auto& i : doc.imports) out << i.fileGuid.string() << " " << i.classGuid.string() << '\n';
    for (const auto& inst : doc.instances) {
        out << inst.instanceGuid.string() << " " << inst.exported << " ";
        if (inst.object) text(*inst.object, out);
        out << '\n';
    }
    return out.str();
}

// An instance by its guid, or "#N" for the Nth instance (unexported ones all have the zero guid).
ebx::Object& instance(ebx::Document& doc, const std::string& guid) {
    if (guid.starts_with("#")) {
        const auto index = std::stoul(guid.substr(1));
        if (index < doc.instances.size() && doc.instances[index].object) return *doc.instances[index].object;
        throw std::runtime_error("no instance " + guid);
    }
    for (auto& inst : doc.instances)
        if (inst.object && lower(inst.instanceGuid.string()) == lower(guid)) return *inst.object;
    throw std::runtime_error("no instance " + guid);
}
}

int main(int argc, char** argv) {
    if (argc < 4) { std::cerr << "usage: ogcam_build <gameRoot> <edits.txt> <outModDir>\n"; return 2; }
    try {
        const fs::path game = argv[1], data = game / "Data", out = argv[3];
        std::vector<std::pair<std::string, std::string>> targets;   // superbundle TOC, bundle
        std::vector<AssetEdit> edits;
        {
            std::ifstream in(argv[2]);
            std::string line;
            while (std::getline(in, line)) {
                if (const auto start = line.find_first_not_of(" \t"); start == std::string::npos || line[start] == '#') continue;
                std::istringstream words(line);
                std::string verb;
                if (!(words >> verb)) continue;
                if (verb == "target") { targets.emplace_back(); words >> targets.back().first >> targets.back().second; }
                else if (verb == "asset") {
                    std::string name;
                    words >> name;
                    // Several blocks for one asset are one edit: each edit starts from the game's copy.
                    const auto same = std::ranges::find_if(edits, [&](const AssetEdit& e) { return lower(e.name) == lower(name); });
                    if (same == edits.end()) edits.push_back({name});
                    else std::rotate(same, same + 1, edits.end());
                }
                else if (verb == "set" || verb == "append") {
                    Set s{verb};
                    words >> s.guid >> s.path >> s.value;
                    edits.back().sets.push_back(s);
                }
                else throw std::runtime_error("unknown line: " + line);
            }
        }
        auto layout = dingosdk::vfs::read_layout(data / "layout.toc");
        CasStore store(data, out / "_unused", layout.root);

        fs::remove_all(out / "Win32");
        std::map<std::string, std::uint64_t> casSize;
        const auto append = [&](std::uint32_t chunk, std::span<const std::byte> bytes) {
            const auto path = out / "Win32" / fs::path(store.directory(chunk)) / "cas_01.cas";
            fs::create_directories(path.parent_path());
            std::ofstream file(path, std::ios::binary | std::ios::app);
            file.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
            auto& at = casSize[path.string()];
            fb::BundleFileInfo info{{true, chunk, 1}, static_cast<std::uint32_t>(at), static_cast<std::uint32_t>(bytes.size())};
            at += bytes.size();
            return info;
        };

        std::map<std::string, std::vector<fb::TocBundle>> tocs;      // superbundle -> its patched bundles
        std::map<std::string, std::size_t> applied;                    // asset -> bundles it was changed in
        std::map<std::pair<std::string, fb::Sha1>, fb::Sha1> shipped;  // (asset, game sha1) -> what that copy becomes
        for (const auto& [superbundle, bundleName] : targets) {
            const auto gameToc = fb::read_toc(read_file(data / fs::path(superbundle)));
            const fb::TocBundle* bundle = nullptr;
            for (const auto& b : gameToc.bundles) if (lower(b.name) == lower(bundleName)) bundle = &b;
            if (!bundle) throw std::runtime_error("bundle not found: " + bundleName);
            auto listing = list_bundle(store, data, data, *bundle, game);
            if (!listing || listing->first != 1) throw std::runtime_error(bundleName + " has no cas manifest");
            if (fb::write_binary_bundle(listing->manifest) !=
                store.read(data, listing->files[0].location, listing->files[0].offset, listing->files[0].size))
                std::cout << "note: " << bundleName << " manifest does not round-trip byte for byte\n";
            std::cout << "== " << bundleName << "\n";

            auto files = listing->files;
            auto manifest = listing->manifest;
            for (const auto& edit : edits) {
                std::size_t index = manifest.ebx.size();
                for (std::size_t i = 0; i < manifest.ebx.size(); ++i)
                    if (lower(manifest.ebx[i].name) == lower(edit.name)) index = i;
                if (index == manifest.ebx.size()) continue;
                const auto original = read_asset(store, data, data, *listing, index, game);
                auto doc = ebx::read_document(original);
                if (const auto again = ebx::write_document(doc); again != original &&
                    text(ebx::read_document(again)) != text(doc))
                    throw std::runtime_error(edit.name + ": the writer changes its contents");
                for (const auto& s : edit.sets) {
                    auto& value = navigate(instance(doc, s.guid), s.path);
                    if (s.verb == "append") {
                        auto* array = std::get_if<ebx::Value::Array>(&value.data);
                        if (!array) throw std::runtime_error(s.path + " is not a list");
                        if (std::ranges::none_of(*array, [&](const ebx::Value& e) {
                                const auto* text = std::get_if<std::string>(&e.data);
                                return text && *text == s.value; }))
                            array->push_back(ebx::Value{s.value});
                        if (!applied[edit.name]) std::cout << "  " << edit.name << " " << s.path << " += " << s.value << "\n";
                        continue;
                    }
                    const auto before = describe(value);
                    assign(value, s.value);
                    if (!applied[edit.name])
                        std::cout << "  " << edit.name << " " << s.path << ": " << before << " -> " << describe(value) << "\n";
                }
                const auto rebuilt = ebx::write_document(doc);
                // Read back what will ship and check every edit landed.
                auto check = ebx::read_document(rebuilt);
                if (text(check) != text(doc)) throw std::runtime_error(edit.name + ": the edited document reads back different");
                const auto sha = sha1_of(rebuilt);
                // Every bundle's copy of the asset must come out the same.
                if (const auto [at, fresh] = shipped.emplace(std::pair{edit.name, manifest.ebx[index].sha1}, sha); !fresh && at->second != sha)
                    throw std::runtime_error(edit.name + ": the copy in " + bundleName + " differs from the others");
                auto& slot = files[listing->first + index];
                slot = append(slot.location.installChunk, fb::encode_cas(rebuilt, {game}));
                manifest.ebx[index].sha1 = sha;
                manifest.ebx[index].originalSize = rebuilt.size();
                ++applied[edit.name];
            }
            files[0] = append(files[0].location.installChunk, fb::write_binary_bundle(manifest));
            tocs[superbundle].push_back({bundle->name, fb::write_bundle_region(files, {}), bundle->loadFlag});

            // Read the bundle back the way the merge does.
            const auto modListing = list_bundle(store, out, data, tocs[superbundle].back(), game);
            if (!modListing) throw std::runtime_error("the written bundle cannot be listed");
            for (std::size_t i = 0; i < modListing->manifest.ebx.size(); ++i) {
                const auto& a = modListing->manifest.ebx[i];
                if (a.sha1 == listing->manifest.ebx[i].sha1) continue;
                const auto bytes = read_asset(store, out, data, *modListing, i, game);
                if (sha1_of(bytes) != a.sha1) throw std::runtime_error(a.name + ": sha1 does not match its payload");
                (void)ebx::read_document(bytes);
                std::cout << "  changed " << a.name << '\n';
            }
        }
        for (const auto& [superbundle, bundles] : tocs) {
            const auto tocPath = out / fs::path(superbundle);
            fs::create_directories(tocPath.parent_path());
            write_file(tocPath, fb::write_patch_toc(bundles, {}));
            (void)fb::read_toc(read_file(tocPath));
        }
        fs::copy_file(data / "layout.toc", out / "layout.toc", fs::copy_options::overwrite_existing);
        for (const auto& edit : edits) {
            std::cout << edit.name << ": " << applied[edit.name] << " bundle(s)\n";
            if (!applied[edit.name]) throw std::runtime_error(edit.name + " is in none of the target bundles");
        }
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
