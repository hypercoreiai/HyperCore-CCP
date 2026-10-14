// include/hypercore/kernels/q8_1_il_copy.hpp - the interleaved activation copy behind
// HYPERCORE_MMVQ_IL (native_mmvq.hpp), as one object instead of a flag threaded through a
// window's call sites.
//
// native_mmvq_il reads 2..8 activation columns from one interleaved copy of their q8_1
// blocks.  That copy belongs to exactly one (n_in, ncols) shape and to the exact bytes it was
// built from: a write to the columns, or a call with a different shape, makes it stale, and a
// stale copy multiplies one layer's weights against another layer's activations - which is what
// the garbled thinking in a Q2_0 run looked like.  read() rebuilds it whenever either changes,
// so the only thing a caller has to remember is invalidate() at every write to the columns.
//
// The engine's verify window is a captured CUDA graph: read() runs at capture time and the
// interleave kernel it launches becomes part of the graph, so a replayed window rebuilds the
// copy exactly as the captured one did.
#pragma once

#include "hypercore/kernels/native_mmvq.hpp"

#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>

namespace hypercore::kernels {

/// The interleaved copy of a window's q8_1 columns.  buffer must be native_q8_1_il_bytes(max_in,
/// max_cols) wide, which is what Verifier::init carves when HYPERCORE_MMVQ_IL is on.
///
/// max_cols is the widest window the engine can build: a --spec 4 verify stage with an MTP draft head is six
/// tokens, so a four-column ceiling here is what made that combination throw at startup.  The copy's lanes are
/// native_q8_1_il_cp(max_cols) wide - 2 for 1-2 columns, 4 for 3-4, 8 for 5-8 - so a buffer sized for
/// (max_in, max_cols) holds every shape up to max_cols; which of them native_mmvq_il has a kernel for is a
/// separate question it answers itself (native_mmvq_il_supported).
class Q81IlCopy {
public:
    static constexpr int kMaxCols = 8;   // native_mmvq's own column ceiling

    void init(void* buffer, int max_in, int max_cols) {
        if (max_in < 32 || max_cols < 1 || max_cols > kMaxCols)
            throw std::invalid_argument("Q81IlCopy::init needs 32+ rows and 1.." + std::to_string(kMaxCols) + " columns");
        buf_ = static_cast<uint8_t*>(buffer);
        max_in_ = max_in;
        max_cols_ = max_cols;
        reset();
    }
    bool armed() const { return buf_ != nullptr; }

    /// A fresh window: nothing is valid until a call builds it.
    void reset() { valid_ = false; n_in_ = 0; ncols_ = 0; builds_ = 0; uses_ = 0; }

    /// Every write to the source columns must call this; a copy built before it is stale.
    void invalidate() { valid_ = false; }

    /// HYPERCORE_MMVQ_IL_REUSE=0: build the copy for every interleaved call, so a call never reads one
    /// made earlier in the window.  The isolation arm: a window that garbles with reuse on and not with
    /// it off has a write that missed invalidate(); one that garbles either way has a kernel that is not
    /// native_mmvq's.
    void set_reuse(bool on) { reuse_ = on; }
    bool reuse() const { return reuse_; }

    /// Tests with no card: swap in a host model of native_q8_1_interleave's layout and the state
    /// machine below can be walked on ordinary memory.
    using Builder = void (*)(const void*, void*, int, int, void*);
    void set_builder(Builder b) { builder_ = b; }

    /// The activations an interleaved kernel should read for (n_in, ncols): the copy, built
    /// from x_q8_1 when its shape or contents changed; the plain blocks for one column.
    const void* read(const void* x_q8_1, int n_in, int ncols, void* stream) {
        if (ncols < 2) return x_q8_1;   // one column: native_mmvq_il reads the plain blocks.  Nothing here
                                        // touches the copy, so one built for a wider shape stays valid; the
                                        // shape check below is what catches a call for a different one.
        if (n_in > max_in_ || ncols > max_cols_)
            throw std::invalid_argument("Q81IlCopy::read: the buffer is sized for " +
                                       std::to_string(max_in_) + " x " + std::to_string(max_cols_));
        if (!reuse_ || !valid_ || n_in_ != n_in || ncols_ != ncols) {
            builder_(x_q8_1, buf_, n_in, ncols, stream);
            valid_ = true; n_in_ = n_in; ncols_ = ncols;
            ++builds_;
        } else {
            ++uses_;
        }
        return buf_;
    }

    int64_t builds() const { return builds_; }   ///< copies built in this window
    int64_t uses() const { return uses_; }       ///< calls that reused one
    bool valid() const { return valid_; }
    int shape_n_in() const { return n_in_; }
    int shape_ncols() const { return ncols_; }

private:
    uint8_t* buf_ = nullptr;
    int max_in_ = 0, max_cols_ = 0;
    int n_in_ = 0, ncols_ = 0;
    bool valid_ = false, reuse_ = true;
    Builder builder_ = native_q8_1_interleave;
    int64_t builds_ = 0, uses_ = 0;
};

}  // namespace hypercore::kernels
