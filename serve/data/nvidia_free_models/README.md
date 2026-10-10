# NVIDIA NIM free-endpoint catalogue (archived)

Snapshot of every model card that build.nvidia.com lists under the **Free Endpoint** facet,
captured 2026-10-09 with the `scrape` MCP server (`SCRAPE_DIR: $HOME/downloads`).

Source filter: `https://build.nvidia.com/models?filters=nimType%3Anim_type_preview`
→ "Filters (1) — 38 models", two pages (24 + 14). Facets seen: Free Endpoint 38,
Partner 14, Download Available 23. Publishers: NVIDIA 25, Meta 4, Google 3, Z.ai 2, OpenAI 1.
Machine-readable catalogue index: `https://build.nvidia.com/models.md` (whole catalogue, ignores
the filter) and `https://build.nvidia.com/llms.txt`.

This directory was moved out of the MCP download scratch area and archived here so the
catalogue survives a downloads clean-up. It is data, not engine source: nothing in `src/`,
`include/` or `serve/` reads it. The only model-list that the engine consumes is
`serve/assist_fast_models.json`, written by `tools/assist_latency_probe.py`.

## Layout

| Path | Contents |
|---|---|
| `free_endpoints_catalog.md` | The consolidated catalogue: 38 cards grouped by type (text/reasoning 17, vision/perception 7, speech/audio 5, image/video generation 6, other), with publisher, parameter count, context length, modalities, licence. |
| `nvidia_free_endpoints.csv` | The same rows as CSV. |
| `_index.json` | 38 records: slug, title, publisher, updated, params, ctx, arch, input, output, licence, release, description. |
| `_unified.json` | 38 records merged from the markdown cards and the HTML pages: slug, name, card_chars, desc, params, active, context, archtype, input, output, licence, geo. |
| `_catalog_rows.json` | The final table rows only (slug, params, ctx, input, output). |
| `_specs.json` | Raw spec/section text scraped per card, before parsing. |
| `_cards_combined.json`, `_final_cards.json`, `_free_cards.json`, `_html_cards.json` | Intermediate merges kept for provenance. |
| `cards/` | Per-model card dumps: `*.md` (YAML front matter + Model Overview / Licence / Deployment Geography / Release Date / Architecture / Size / Context / Modalities) and `card_*.txt` (visible text of the eight cards whose canonical path is `/qc69jvmznzxy/<slug>.md`, which return an HTML shell instead of markdown when fetched as `.md`). |
| `derived/` | Working tables and reports from the passes that produced the catalogue. |
| `raw/` | 54 unmodified page fetches (15 MB). Regenerable, so it is gitignored. |
| `scripts/` | The one-off extractors used to build the catalogue (`parse_cards.py`, `extract.py`, `consolidate*.py`, `unified.py`, `build_final.py`, `catalog.py`, `make_doc.py`, `fetch_specs.py`, `rsc_extract.py`). Kept so the snapshot can be reproduced. |

## Regenerating

```
python3 scripts/fetch_specs.py          # refetch the cards into the scrape download dir
python3 scripts/parse_cards.py          # front matter -> _index.json
python3 scripts/unified.py              # merge md + html -> _unified.json
python3 scripts/build_final.py          # -> _catalog_rows.json
python3 scripts/make_doc.py             # -> free_endpoints_catalog.md
```

Scripts write to the scrape server's download directory, not here — rerun them with the
cwd set to a scratch folder, then copy the outputs back.
