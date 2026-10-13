// src/program/batch_groups_test.cpp - how many pipelined slot groups --batch runs with (header-only, CPU).
//
//   1. `auto` picks the most groups, at most one per stage, that divide the slots;
//   2. a layer split with --batch >= 2 and no --batch-groups means the auto default;
//   3. the pipeline wins over --batch-mtp: the default groups stay and generate.cpp turns --batch-mtp off.
//      mtp_serial (HYPERCORE_BATCH_MTP_SERIAL=1) or --batch-groups 1 keeps the serial MTP windows instead;
//   4. --adapt-async 1 still gives one group;
//   5. a number or `auto` given explicitly is honoured, with or without those features;
//   6. no layer split: the number given (1) stays.
//
// Build and run standalone:
//   g++ -std=c++17 -I include src/program/batch_groups_test.cpp -o /tmp/batch_groups_test && /tmp/batch_groups_test
#include "hypercore/program/batch_groups.hpp"

#include <cstdio>

namespace bg = hypercore::program::batch_groups;

namespace {
int g_fail = 0;

void check(bool ok, const char* what) {
    std::printf("  %-78s %s\n", what, ok ? "ok" : "FAIL");
    if (!ok) ++g_fail;
}

/// A layer split with `stages` stages after CUDA0 and `batch` slots, nothing else given.
bg::Input in(int batch, int stages) {
    bg::Input i;
    i.batch = batch;
    i.later_stages = stages;
    return i;
}
}  // namespace

int main() {
    std::printf("batch_groups_test\n");

    check(bg::auto_groups(0, 4) == 1, "auto: no layer split, one group");
    check(bg::auto_groups(1, 2) == 2 && bg::auto_groups(1, 4) == 2 && bg::auto_groups(1, 3) == 1,
          "auto: two GPUs, 2 groups when the slots divide by 2");
    check(bg::auto_groups(3, 8) == 4 && bg::auto_groups(3, 6) == 3 && bg::auto_groups(3, 2) == 2,
          "auto: at most one group per GPU, and a divisor of the slots");

    {   // the default: a layer split with --batch pipelines one group per stage
        const auto r = bg::resolve(in(2, 1));
        check(r.groups == 2 && r.from_auto && r.serial == bg::Serial::None,
              "layer split, --batch 2, nothing given: 2 groups");
    }
    {
        const auto r = bg::resolve(in(1, 1));
        check(r.groups == 1 && !r.from_auto, "--batch 1: no default");
    }
    {
        const auto r = bg::resolve(in(2, 0));
        check(r.groups == 1 && !r.from_auto, "no layer split: one group");
    }

    {   // the production shape: parallel 2 on a 2-GPU split with --batch-mtp: the pipeline wins
        bg::Input i = in(2, 1);
        i.batch_mtp = true;
        const auto r = bg::resolve(i);
        check(r.groups == 2 && r.from_auto && r.serial == bg::Serial::None && r.would_be == 2,
              "--batch-mtp, nothing given: the default groups stay, no serial reason");
    }
    {   // HYPERCORE_BATCH_MTP_SERIAL=1 keeps the serial MTP windows: one group, and the reason is named
        bg::Input i = in(2, 1);
        i.batch_mtp = true;
        i.mtp_serial = true;
        const auto r = bg::resolve(i);
        check(r.groups == 1 && r.from_auto && r.serial == bg::Serial::BatchMtp && r.would_be == 2,
              "--batch-mtp + HYPERCORE_BATCH_MTP_SERIAL=1: one group, because of --batch-mtp");
        check(bg::serial_what(r.serial)[0] == '-', "the reason names the feature");
    }
    {   // the serial flag on its own does nothing: no --batch-mtp, no reason to give way
        bg::Input i = in(2, 1);
        i.mtp_serial = true;
        const auto r = bg::resolve(i);
        check(r.groups == 2 && r.serial == bg::Serial::None,
              "HYPERCORE_BATCH_MTP_SERIAL without --batch-mtp: 2 groups");
    }
    {
        bg::Input i = in(2, 1);
        i.adapt_async = true;
        const auto r = bg::resolve(i);
        check(r.groups == 1 && r.serial == bg::Serial::AdaptAsync, "--adapt-async 1, nothing given: one group");
    }
    {
        bg::Input i = in(2, 1);
        i.batch_mtp = true;
        i.adapt_async = true;
        check(bg::resolve(i).serial == bg::Serial::AdaptAsync,
              "both, no serial flag: --batch-mtp is off, --adapt-async 1 still gives one group");
        i.mtp_serial = true;
        check(bg::resolve(i).serial == bg::Serial::BatchMtp, "both with the serial flag: --batch-mtp is named");
    }
    {   // nothing to give way: the slots do not divide, so auto is one group anyway and there is nothing to say
        bg::Input i = in(3, 1);
        i.batch_mtp = true;
        i.mtp_serial = true;
        const auto r = bg::resolve(i);
        check(r.groups == 1 && r.serial == bg::Serial::None && r.would_be == 1,
              "auto would be 1 group anyway: no reason");
    }
    {   // explicit values are honoured
        bg::Input i = in(4, 1);
        i.set = true;
        i.given = 2;
        i.batch_mtp = true;
        i.adapt_async = true;
        i.mtp_serial = true;
        const auto r = bg::resolve(i);
        check(r.groups == 2 && !r.from_auto && r.serial == bg::Serial::None, "--batch-groups 2 with --batch-mtp: 2");
        i.given = 1;
        check(bg::resolve(i).groups == 1, "--batch-groups 1: 1 (the opt-out, keeps the serial windows)");
        i.given = 4;   // not checked here: generate.cpp refuses what does not divide
        check(bg::resolve(i).groups == 4, "--batch-groups 4 is returned as given");
    }
    {
        bg::Input i = in(2, 1);
        i.set = true;
        i.auto_given = true;
        i.batch_mtp = true;
        const auto r = bg::resolve(i);
        check(r.groups == 2 && r.from_auto && r.serial == bg::Serial::None,
              "--batch-groups auto with --batch-mtp: auto asked for the pipeline, 2 groups");
    }
    {
        bg::Input i = in(2, 0);
        i.set = true;
        i.given = 1;
        check(bg::resolve(i).groups == 1, "one GPU: the given 1 stays");
    }

    std::printf("%s: %d check%s %s\n", g_fail ? "FAIL" : "ok", g_fail, g_fail == 1 ? "" : "s",
                g_fail ? "failed" : "all passed");
    return g_fail ? 1 : 0;
}
