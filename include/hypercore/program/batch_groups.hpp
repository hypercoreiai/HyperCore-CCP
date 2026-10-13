// include/hypercore/program/batch_groups.hpp - how many pipelined slot groups `--batch` runs with.
//
// `--batch-groups N` pipelines N groups of slots through the stages of a layer split; `--batch-groups auto` picks the
// most groups (at most one per stage) that divide the slots.  A layer split with `--batch` >= 2 and no
// `--batch-groups` at all means `auto`.  The pipelined path runs neither `--batch-mtp`'s drafts nor the batch
// adaptive tier (`--adapt-async 1` between batch windows), so when one of those is asked for and the number of groups
// was NOT given, `auto` resolves to one group (the serial windows they run in) and says why.  `--batch-mtp` keeps
// those serial windows only when asked for: `HYPERCORE_BATCH_MTP_SERIAL=1` (the older `STRATA_BATCH_MTP_SERIAL` is
// read as the same knob) or `--batch-groups 1`.  `--adapt-async 1` still gives one group.  A number or `auto` given
// on the command line is honoured as before.
//
// Pure (no GPU, no environment read): generate.cpp passes in what it knows, so this is testable on a CPU alone.
#pragma once

namespace hypercore::program::batch_groups {

/// What made the default `auto` give way to the serial windows.
enum class Serial { None, BatchMtp, AdaptAsync };

struct Input {
    bool set = false;          ///< --batch-groups was given (a number or `auto`)
    bool auto_given = false;   ///< ... as `auto`
    int given = 1;             ///< the number given (1 when none)
    int batch = 0;             ///< the slots
    int later_stages = 0;      ///< the layer split's stages after CUDA0 (0: no layer split)
    bool batch_mtp = false;    ///< --batch-mtp is on (it passed the gates that do not concern the groups)
    bool mtp_serial = false;   ///< HYPERCORE_BATCH_MTP_SERIAL=1: keep --batch-mtp's serial windows
    bool adapt_async = false;  ///< --adapt-async 1 was asked for
};

struct Result {
    int groups = 1;
    bool from_auto = false;           ///< the number came from `auto` (given, or the layer-split default)
    Serial serial = Serial::None;     ///< `auto` would have pipelined, but this feature needs the serial windows
    int would_be = 1;                 ///< what `auto` would have picked without it (== groups unless `serial`)
};

/// The most groups, at most one per stage of the layer split (`later_stages` + 1 GPUs), that divide `batch`.
inline int auto_groups(int later_stages, int batch) {
    int best = 1;
    if (later_stages <= 0) return best;
    for (int d = 2; d <= later_stages + 1 && d <= batch; ++d)
        if (batch % d == 0) best = d;
    return best;
}

inline Result resolve(const Input& in) {
    Result r;
    r.groups = in.given;
    r.would_be = in.given;
    const bool defaulted = !in.set && in.later_stages > 0 && in.batch > 1;   // nothing given: the auto default
    if (!in.auto_given && !defaulted) return r;
    r.from_auto = true;
    r.would_be = auto_groups(in.later_stages, in.batch);
    r.groups = r.would_be;
    if (!in.set && r.would_be > 1) {   // only the default gives way; `--batch-groups auto` asked for the pipeline
        // --batch-mtp no longer gives way on its own: it keeps the serial windows only when asked for
        // (HYPERCORE_BATCH_MTP_SERIAL=1, or `--batch-groups 1`, which is `in.set` and never reaches here).
        if (in.batch_mtp && in.mtp_serial) r.serial = Serial::BatchMtp;
        else if (in.adapt_async) r.serial = Serial::AdaptAsync;
        if (r.serial != Serial::None) r.groups = 1;
    }
    return r;
}

/// The feature that asked for the serial windows, for the start-up line.
inline const char* serial_what(Serial s) {
    return s == Serial::BatchMtp ? "--batch-mtp" : s == Serial::AdaptAsync ? "--adapt-async 1" : "";
}

}  // namespace hypercore::program::batch_groups
