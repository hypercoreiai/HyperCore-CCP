// #2055: which build creates the MTP drafter's branch stream.  Pure string logic, so it runs on any machine: the
// default follows the AMD architecture, and HYPERCORE_MTP_SIDE_STREAM overrides it in both directions.
#include "hypercore/core/mtp_side_stream.hpp"

#include <cstdio>

using hypercore::core::mtp_side_stream_on;

static int fails = 0;
#define CHECK(c) do { if (!(c)) { std::fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); ++fails; } } while (0)

int main() {
    // the default: gfx103x yes, everything else no
    CHECK(mtp_side_stream_on("gfx1030", nullptr));
    CHECK(mtp_side_stream_on("gfx1031", nullptr));
    CHECK(mtp_side_stream_on("gfx1032", nullptr));
    CHECK(mtp_side_stream_on("gfx1030:sramecc-:xnack-", nullptr));   // the feature suffix does not hide the part
    CHECK(!mtp_side_stream_on("gfx1100", nullptr));
    CHECK(!mtp_side_stream_on("gfx1151", nullptr));
    CHECK(!mtp_side_stream_on("gfx1201", nullptr));
    CHECK(!mtp_side_stream_on("gfx906", nullptr));
    CHECK(!mtp_side_stream_on("gfx1035", nullptr));   // RDNA2 but not the gfx103 line; unmeasured, so off
    CHECK(!mtp_side_stream_on("", nullptr));
    CHECK(!mtp_side_stream_on(nullptr, nullptr));     // no device read: the safe, unchanged behaviour

    // the override wins in both directions, and beats the arch
    CHECK(mtp_side_stream_on("gfx1100", "1"));
    CHECK(!mtp_side_stream_on("gfx1030", "0"));
    CHECK(mtp_side_stream_on("gfx906", "1"));
    CHECK(mtp_side_stream_on("gfx1030", ""));        // an empty value is not a value: the default stands
    CHECK(mtp_side_stream_on("gfx1100", "2"));       // any non-zero is "on", as with the other switches

    if (fails) { std::fprintf(stderr, "mtp_side_stream_test: %d check(s) failed\n", fails); return 1; }
    std::printf("mtp_side_stream_test: ok\n");
    return 0;
}
