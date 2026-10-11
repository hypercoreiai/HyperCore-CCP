# General knowledge outside the project

Accumulated from 6 transcripts, 15 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


## Current state

Maintained by hand; the builder keeps it in place.

**lm-evaluation harness.** The suite is the reference for the model's public numbers; the chats
established which subsets are actually runnable here and that a score without the subset named is
not comparable.

**Handbrake and Ghidra.** Both were installed and used; the notes are about the CLI flags that
worked on this box, not the tools in general.

**The Twitter export.** A per-account extract; the finding that mattered is that the account's
activity is replies rather than posts, which changed how the profile was described.

**Superconductivity.** An ab-initio Tc prediction for an unsynthesized compound is not currently
achievable to ±10 K; DFPT phonons → Eliashberg/Allen–Dynes gives `ω_log` and `λ` from first
principles, and that is the limit of what can be claimed.

**General rule for this file:** a fact belongs here only if it changed something in the project.
Anything else stays in the transcript.


## What is true now

how the thing works, as the chats established it


**--batch**
- If you meant HandBrake for video — I'm familiar with it: CLI is `handbrake -i input.mkv -o output.mp4 -e x265 -q 22`, presets live in `~/.config/HandBrake` on Linux, and batch queueing is via the queue UI or `--batch`.
  <sub>2026-10-04 · strata-chat-2026-10-04-07-56.md</sub>

**--min-save**
- For every file it copies a keyframe-exact segment (`-c copy`, so the original bits are preserved), then re-encodes that segment with libx265 — the same encoder HandBrake uses — starting at RF 26 and stepping up to RF 30 until the measured byte saving reaches `--min-save`.
  <sub>2026-10-04 · strata-chat-2026-10-04-07-56.md</sub>

**caveat pytest default**
- One caveat: pytest's default tmpdir on this box is owned by another user, so run it as `TMPDIR=/home/ai-user0/twitter_extract/.tmp pytest test_extract_tweets.py`.
  <sub>2026-10-07 · strata-chat-2026-10-07-20-11.md</sub>

**cost optimality certified**
- If `Cost(p) = LB`, optimality is certified, not merely "no improvement found." Prior work this builds on honestly: CompCert's verified transformations, Razor (verified C rewriting), and the verified-algorithmic-skeletons line (Bannister et al., 2021).
  <sub>2026-10-07 · strata-chat-2026-10-07-18-16.md</sub>

**details summary tool**
- <details><summary>Tool browse</summary> ``` https://raw.githubusercontent.com/NationalSecurityAgency/ghidra/Ghidra_12.1.4_build/Ghidra/Configurations/Public_Release/src/global/docs/WhatsNew.md Ghidra is a software reverse engineering (SRE) framework developed by NSA's Research Directorate.
  <sub>2026-10-07 · strata-chat-2026-10-07-18-39.md</sub>

**genuinely want image**
- If you genuinely want image transcoding (batch convert/re-encode/rescale), the usual tools are ImageMagick (`magick input.png -quality 85 out.jpg`), ffmpeg (`ffmpeg -i in.png out.webp` — ffmpeg does handle images despite HandBrake not),GraphicsMagick, cwebp / libjpeg-turbo, or Pillow in Python.
  <sub>2026-10-04 · strata-chat-2026-10-04-07-56.md</sub>

**ghidra.net**
- Downloads and docs are at the GitHub releases page [2] and `ghidra.net` / `nsa.gov`'s Ghidra page, which now redirect to the GitHub repository [1][6]; distro packages (Arch, Chocolatey, Homebrew, Flatpak) exist but lag the official release by a version or two (third-party trackers, Low confidence on currency).
  <sub>2026-10-07 · strata-chat-2026-10-07-18-39.md</sub>

**items carry media**
- 143 items carry media; no native retweets or quotes in this export (`"retweeted": true` count is 0) — the `RT [handle]:` items are manual retweets and are classified as originals
  <sub>2026-10-07 · strata-chat-2026-10-07-20-11.md</sub>

**json.loads**
- The tweets are not plain JSON; each file is a JS assignment: So the extraction is: strip the `window.YTD.… =` prefix → `json.loads` → normalise each entry.
  <sub>2026-10-07 · strata-chat-2026-10-07-20-11.md</sub>

**out/threads.md**
- Outputs written: `out/tweets.jsonl` (1.93 MB), `out/tweets.csv` (934 KB), `out/threads.md` (936 KB, 3695 conversations, longest is 2 items)
  <sub>2026-10-07 · strata-chat-2026-10-07-20-11.md</sub>

**retweet legacy shape**
- (`{"retweet": {…}}` is the legacy shape, handled too.)
  <sub>2026-10-07 · strata-chat-2026-10-07-20-11.md</sub>

## Measured on this machine

numbers actually measured, not estimated


**according mckinsey state**
- According to McKinsey's State of AI survey, 88% of organisations use AI in at least one business function and 62% are experimenting with agents, yet only 23% are scaling agents in even one function and fewer than 10% across multiple functions.
  <sub>2026-10-03 · strata-chat-2026-10-03-12-03.md</sub>

**fixture deterministic runs**
- With the 40 ms fixture that's deterministic (10/10 runs).
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**verdict give defensible**
- Verdict: I can give a defensible probabilistic forecast, but the honest headline is that the dominant uncertainty is observational, not mechanistic. Forecast under stated pathways. IPCC AR6 gives a likely decline of ~34% (10–43%) by 2100 under high emissions, and explicitly states low confidence in collapse.
  <sub>2026-10-07 · strata-chat-2026-10-07-18-16.md</sub>

## Gotchas

things that bit once and will bite again


**know tool called**
- I don't know a tool called "Hanbrake" — the searches only return HandBrake, which is a video transcoder (open-source, GPLv2, Windows/Mac/Linux; FFmpeg + x264/x265/SVT‑AV1 backends, outputting MP4/MKV/WebM; source support includes DVD/Blu‑ray, MXF, MPEG‑TS, QuickTime, ProRes, DNxHD/HR, XAVC, AVCHD).
  <sub>2026-10-04 · strata-chat-2026-10-04-07-56.md</sub>
