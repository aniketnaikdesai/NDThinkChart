# Investigation — candles overlapping in price **and** volume

**Reviewer:** Code Reviewer (subagent) · **Date:** 2026-10-15
**Report under review:** *"why the candles are overlapping — in price **and** in volume"* — symbol `SPY`, TF `5 mins`, Mode `Candles`, **Ext Hours ON**.
**Concurrency note:** another reviewer session (footprint entitlements) is running and may append to `escalations.json`. **This file is the only artifact written by this review**; `escalations.json` and `review_log.md` were **not** touched. Proposed escalation id is stated in §8 for later merging.

---

## 1. Plain-language answer

The overlap is **not** a collapse problem and **not** the footprint overlay. It is the **D6 "4-device-pixel minimum" candle body floor** being applied *unconditionally*, with no cap relative to the distance between bars:

- `ui/candlestick_item.py:122-138` raises every candle body's half-width to `min_w = 2.0 / px_per_sec` — a **4 device-pixel-wide body** — whenever the natural body is narrower.
- `ui/chart_panel.py:1688-1690` reuses that same floor for the volume bars (`w_vol = self._clamp_half_width(...)`, `width=w_vol*2`).

When the plotted bars are dense enough that their **pitch drops below 4 device pixels** — which a 5-min Ext-Hours view does (pre/post-market roughly doubles the bar count) — the code forces every body/bar to 4 px on a <4 px pitch, so **each bar is wider than the gap to its neighbour and they overlap**. Because the same floor feeds both panes, price **and** volume overlap identically.

The 35%-gap formula (`median_diff * 0.325`) is *correct* and *collapse-consistent* — the bug is that the 4 px floor then **overrides it upward past the pitch**.

---

## 2. The user's leads, adjudicated

| # | Lead | Verdict |
|---|---|---|
| 1 | widths in raw time units vs collapsed axis (prime suspect) | **FALSIFIED.** Widths are computed in **display-x (collapsed) units** and agree with the axis. Measured `_candle_half_width = 97.5 = 0.325 × 300` (the display median spacing). See §3. |
| 2 | present with Ext Hours OFF too? | **Only with Ext Hours ON.** With Ext OFF the RTH-only filter halves the bar count (192 → 78), so the pitch stays >4 px and there is no overlap. The trigger is **density**, not collapse. |
| 3 | footprint overlay drawing over the candles? | **RULED OUT.** Reproduced with **no footprint overlay active** (Mode `Candles`, no footprint entries) — the price pane still merges. It is the `CandlestickItem` + `volume_bars` items. |
| 4 | reproduce & measure offscreen | **DONE** — numbers in §3. |
| 5 | D6 4 px minimum interacting with the collapsed axis; D9 inheriting it | **CONFIRMED** for the *floor* (see §3), but the clamp itself **is** computed against the *collapsed* ViewBox range (not a stale uncollapsed range). D9 correctly inherits whatever the price body is — it inherits the *over-wide* floor. |
| 6 | does it contradict a written AC? | **YES** — see §6. |

---

## 3. Measured evidence (offscreen reproduction, no footprint, no live data)

Harness: `QT_QPA_PLATFORM=offscreen`, `ChartPanel` 600 px tall, `set_symbol("SPY")`, `set_timeframe("5 mins")`, `update_chart(...)` with synthetic SPY-like 5-min bars (ET sessions 04:00–20:00, uniform 300 s). Widths measured **from the rendered `QPicture` bounding rect** (`panel.candlestick.boundingRect()` minus the drawn display-x span), and by pixel-scanning the rendered price viewport — the same method as `tests/test_chart_dpi.py`.

### 3a. The reported case — SPY 5-min, Ext Hours ON, one session, 192 bars, 900 px pane

| quantity | value |
|---|---|
| view x-span (display units) | 63 918 |
| px per display-unit | 0.01278 |
| inter-bar **pitch** on screen | **3.83 px** |
| cached `_candle_half_width` (natural, 35 % gap) | 97.5 → full body **195** display-units = **2.44 px** |
| **rendered** candle body (D6 floor) | **4.00 device px**  ← floor overrode the 35 %-gap value |
| rendered **volume** bar width | **4.00 device px** (same floor) |
| pixel-scan of the price pane through the bodies | **1 contiguous run of 738 px — zero visible gap** |

So on the exact reported chart the candle bodies are forced wider than their 3.83 px pitch and, because bodies are opaque and axis-aligned with antialiasing off (`candlestick_item.py:87`), a sub-pixel geometric overlap (0.17 px) is enough to **eliminate the gap entirely** — every bar merges into the next. The volume pane is byte-for-byte identical (4.00 px bars on the same pitch).

**Conclusion on lead 1:** the width is in display/collapsed units and matches the axis; there is **no raw-vs-collapsed unit mismatch**. Changing the 5-min *density* (not the collapse) is what makes the floor bite.

### 3b. Ext Hours OFF — same SPY 5-min data, same 900 px pane

| quantity | value |
|---|---|
| bars plotted (RTH only) | 78 |
| pitch | 8.86 px |
| rendered body | 5.79 px (= 0.65 × pitch → 35 % gap) |
| rendered volume width | 5.76 px |
| pixel-scan | 78 separate runs, positive gaps |

No overlap. The Ext-Hours toggle doubles the bar count (adds ~04:00–09:30 and 16:00–20:00 bars), which is what pushes the pitch under 4 px.

### 3c. Body/pitch ratio matrix (rendered body ÷ on-screen pitch; **>1 = overlap**)

Every overlapping cell has the body pinned at exactly **4.00 px** and volume at **4.00 px**:

| pane width | sessions | Ext ON | Ext OFF |
|---|---|---|---|
| 1200 | 1 | 0.77 | 0.65 |
| 900 | 1 | **1.05** | 0.65 |
| 600 | 1 | **1.65** | 0.72 |
| 1200 | 2 | **1.49** | 0.65 |
| 900 | 2 | **2.04** | 0.86 |
| 600 | 2 | **3.23** | **1.35** |
| 1200 | 3 | **2.23** | 0.93 |
| 900 | 3 | **3.04** | **1.27** |
| 600 | 3 | **4.80** | **1.99** |

Worse when narrower or with more sessions — and once ratio > 1 the visual result is a solid band, not merely touching bars.

### 3d. Is the collapse (D21.4) the cause? No.

- A **single-session** view has an *identity* collapse map (`collapse_identity=True`) and **still** overlaps at 900 px (3a) — so the presence of collapse is not what decides it.
- Collapse *removes* non-trading seconds from the span, which **raises** `px_per_data` and therefore the pitch (e.g. two sessions Ext ON: collapsed x-span 124 974 vs a raw span ≈ 144 000 → pitch **1.96 px** collapsed vs **≈1.88 px** uncollapsed). Collapse therefore slightly **mitigates** the overlap; it does not create it.
- The clamp **does** read the collapsed range (`x_span = 63 918` display units), so it is not a stale *uncollapsed* clamp either — it is simply a floor that is too large for the pitch.

---

## 4. Root cause — proved vs inferred

**PROVED (measured):**
1. `ui/candlestick_item.py:136` — `min_w = 2.0 / px_per_sec` forces a **4 device-px body** (`:137-138` `if w < min_w: w = min_w`) with no upper bound tied to the bar pitch. Measured rendered body = 4.00 px on a 3.83 px pitch (§3a).
2. `ui/chart_panel.py:1688` — `w_vol = self._clamp_half_width(self._candle_half_width)` reuses the identical floor (`:1622-1629`, `min_w = 2.0 / (vb.width()/x_span)`), and `:1690` `width=w_vol*2` draws it. Measured volume width = 4.00 px. This is why **volume overlaps exactly like price** (D9 inheritance, lead 5 — the *mechanism* of D9 is fine; it faithfully copies an over-wide body).
3. The natural width is display-correct: `_compute_candle_half_width` (`chart_panel.py:1600-1612`) differences `_to_display(ts)`, giving `97.5 = 0.325 × 300` display-units. No raw-vs-display mismatch (lead 1 falsified).
4. Overlap occurs with **no footprint overlay** (lead 3 ruled out).
5. Overlap occurs whenever rendered body / pitch > 1; all such cells are the D6 floor binding (§3c).

**INFERRED:**
- The real screenshot sits near the mild end of this spectrum (single overnight, ~200 bars at ~900 px ⇒ ratio ≈ 1.05, §3a), where the *geometric* overlap is small but **visually total** because the opaque bodies leave zero gap. Narrower panes or multi-day 5-min Ext-Hours views degrade to the 3–5× smear in §3c.

**Not the cause:** the D21.4 collapse map (`services/time_collapse_service.py`), the volume width inheritance logic per se, and the footprint overlay.

---

## 5. Regression? — No (long-standing defect)

- The unconditional 4 px floor is from **commit `09070e85` (D6, 2026-09-20)** — `git blame` on `candlestick_item.py:122-140`.
- The display-x-aware `_compute_candle_half_width` + `_clamp_half_width` + volume reuse arrived with **D28.4, commit `28c4e693` (2026-10-13)**. The pre-D28.4 code (`git show 28c4e69^:ui/chart_panel.py`) used the *same* `median_… * 0.325` and the *same* `min_w_vol = 2.0/px_per_sec` clamp (against the volume ViewBox), so the volume-side floor overlap pre-dates D28.4 too.
- D21.4 collapse (`286341e`) landed **after** D6 and slightly **reduces** density; it neither introduced nor fixes this.

So this is a **latent design conflict that has been present since D6**, not a regression of D21.4 or D28.4.

---

## 6. Does it contradict a written AC? — Yes

- **AC-D7.1** (`requirements.md:1229`): "…the gap between adjacent bodies is ~35 % of bar spacing". Violated at default zoom for a 5-min Ext-Hours view (rendered gap = 0).
- **D7 Edge Cases** (`requirements.md:1237-1239`): "Very dense 1-min view … the 4px body minimum may override — **the gap remains positive** and the chart does not become empty." Measured gap is **0**, not positive. Violated.
- **AC-D6.4** (`requirements.md:1194-1199`) requires the body to stay `>= 4` **device** pixels at DPR 2, unconditionally. That is in **direct tension** with a positive gap once the pitch < 4 px — both cannot hold.
- **D9 / AC-D9.1-9.2** (`requirements.md:1370-1375`) is satisfied (volume == price body) — which is precisely *why* volume overlaps too. D9 is correct; it is faithfully copying a body that is already too wide.
- Nothing in `AC-D21.4.*` (`requirements.md:2279-2283`) prescribes a bar width under collapse; `R37` (`requirements.md:3296`) only notes collapse "can affect … the D7/D9 spacing" — **it was flagged as a risk and never verified against density**.

---

## 7. Severity

**Blocking.** In the reported configuration both panes are unreadable (bodies merge; the price pane renders as one continuous band), and it degrades monotonically with density/window width (§3c). It is not a cosmetic nit.

---

## 8. Owner / route and proposed escalation id

- **Primary → `BUILD`** (category `bug`, severity `blocking`): make the D6 4 px floor **never exceed the inter-bar pitch** — i.e. keep the gap ≥ 0 (cap the clamped half-width at the pitch-preserving value so `body ≤ pitch`), applied to **both** the candle body and the volume width. Touch points: `ui/candlestick_item.py:122-140` and `ui/chart_panel.py:1614-1632` (`_clamp_half_width`) / `:1688-1690`. This restores the D7 "gap remains positive" edge case.
- **Secondary → `REQUIREMENTS`** (category `consistency`, severity `should-fix`): AC-D6.4's *unconditional* "body ≥ 4 device px at DPR 2" cannot coexist with a positive gap once the pitch < 4 px. The requirements should state which wins at high density (e.g. "4 px floor applies only while the pitch permits a positive gap"). This is a written-AC conflict, not a code decision — do not resolve it in code silently.

**Proposed escalation id: `ESC-041`.** ⚠️ **Collision risk:** the free id was `ESC-040` at the time of writing (11 entries, `ESC-032`–`ESC-040` open). The concurrent footprint-entitlements session may append entries while this review runs, so **re-derive the next free id at merge time** rather than assuming `ESC-041` is free.

---

## 9. Warranted regression test (invariant form)

Add a rendering test (extend `tests/test_volume_width.py`, or replace the string-presence `tests/test_candle_spacing.py`) that asserts, for datasets and pane widths that span the dense regime:

> **Invariant:** for any loaded dataset at any pane width, the **rendered** candle body width (device px, measured from the `CandlestickItem` `QPicture` bounding rect — **never re-derived from the production formula**) is **≤ the inter-bar device-pixel pitch** ⇒ `gap ≥ 0`; and the volume `BarGraphItems` width equals that same body width.

Fixture matrix that exposes it: SPY-like 5-min bars, 1–3 ET sessions, at 600/900/1200 px, **Ext Hours ON and OFF**. In the non-dense regime additionally assert `body ≈ 0.65 × pitch` (the 35 % gap). Do **not** assert `body ≈ 4 px` — that is the very behaviour that is wrong.

**Why the suite is green on this today:**
- `tests/test_candle_spacing.py` is a **string-presence test** (`assert "0.325" in text`); it never renders anything.
- `tests/test_volume_width.py` asserts only *volume == measured candle body* and, in its dense case, *both ≈ 4.0 device px* — it **never relates body width to the pitch/gap**, so it **encodes the 4 px floor as correct**. Its dense fixture (960 × 1-min at 900 px ⇒ pitch ≈ 0.85 px) is a body/pitch ≈ 4.7 maximal overlap and the test **passes**.
- `tests/test_chart_dpi.py` asserts only *body ≥ 4 px* and *body > wick* — again no pitch/gap relation.
- The D7 "gap remains positive" edge case has **no test at all**, so no test can fail.

---

## 10. Housekeeping

- **`docs/code_review/escalations.json` — NOT modified.**
- **`docs/code_review/review_log.md` — NOT modified.**
- No code, requirements, plan, architecture, task, or build file was modified. Only this file (`docs/code_review/candle_overlap_investigation.md`) was written.
