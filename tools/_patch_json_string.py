import pathlib

p = pathlib.Path("/home/ai-user0/HyperCore/src/interface/hypercore_bridge.cpp")
s = p.read_text()
old = """static bool json_string(const std::string& json, const std::string& key, std::string& out) {
    size_t i = json.find(key);
    if (i == std::string::npos) return false;
    i = json.find('"', i + key.size());
    if (i == std::string::npos) return false;
    size_t end = json.find('"', i + 1);
    if (end == std::string::npos) return false;
    out = json.substr(i + 1, end - i - 1);
    return true;
}"""
new = """static bool json_string(const std::string& json, const std::string& key, std::string& out) {
    const std::string needle = "\\"" + key + "\\"";
    size_t i = json.find(needle);
    if (i == std::string::npos) return false;
    i = json.find(':', i + needle.size());   // past the key's own closing quote and the colon
    if (i == std::string::npos) return false;
    i = json.find('"', i + 1);
    if (i == std::string::npos) return false;
    size_t end = json.find('"', i + 1);
    if (end == std::string::npos) return false;
    out = json.substr(i + 1, end - i - 1);
    return true;
}"""
assert old in s
p.write_text(s.replace(old, new, 1))
print("json_string fixed")

t = pathlib.Path("/home/ai-user0/HyperCore/bench/results/2026-10-09-blackbox-api/worker_mode_test.c")
u = t.read_text()
u = u.replace(
    '    check(a.tokens > 0 && b.tokens > 0, "neither stream starved the other");',
    '    check(b.tokens > 0 && a.tokens < b.tokens,\n          "cancel shortened one stream without stopping the other");',
)
t.write_text(u)
print("test assertion fixed")
