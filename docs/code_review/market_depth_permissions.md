# Code Review — "additional market data permissions needed for depth" (error 2152)

Owner question: *"Why am I getting 'additional market data permissions needed for depth'?"*
with the claim *"I have verified that on TWS I am able to open and view market depth Level 2."*

Answer up front: **this is an IBKR account-entitlement condition, not a defect in this repo.**
The app is correctly asking for SMART-aggregated depth; IBKR answers with error **2152** listing the
US venues the account is *not* entitled to. Seeing L2 in the TWS GUI does not imply the API has the
same depth entitlements. There is **one secondary, non-causal handling gap** (below) that I am routing.

> Concurrency note: a parallel Code Reviewer session owns `escalations.json` / `review_log.md`.
> This file is the only artifact this session wrote. Nothing was written to those two files, to code,
> or to requirements/plan/architecture/tasks/build.

---

## 1. What the app actually requests (verified from the repo)

Every `reqMktDepth` call site:

| Call site | contract | `numRows` | `isSmartDepth` | meaning |
|---|---|---|---|---|
| `ibkr/market_depth.py:25` (`MarketDepthManager.subscribe`, the **DOM/Active-Trader** ladder) | `get_contract_for_symbol(symbol)` | 10 | **`False`** | exchange-specific / "direct-routed" depth |
| `ibkr/market_depth.py:65` (`subscribe_shared`, the **D37 heatmap**, main + pop-outs share one feed) | `get_contract_for_symbol(symbol)` | 10 | **`True`** | SMART-aggregated depth |
| `ibkr/market_depth.py:103` (`resubscribe_shared`, replay after reconnect) | same | 10 | **`True`** | SMART-aggregated depth |

- The contract for a stock is built by `get_stock_contract()` with **`exchange="SMART"`**
  (`ibkr/contracts.py:181-187`), selected by `get_contract_for_symbol` (`ibkr/contracts.py:237`);
  futures get a concrete exchange such as `CME` (`ibkr/contracts.py:176-177, 239-242`).
- `numRows`/`num_levels` is 10 at every call site (`ui/ticker_session.py:725, 770`;
  `ui/main_window.py:3004, 3012`).
- So the app makes **both** kinds of request: the heatmap asks for **SMART depth** (`True`), the DOM
  ladder asks for **non-smart depth on a `SMART` contract** (`False`).

## 2. How many / which requests (four reqIds)

`id_manager.get_id()` hands out a fresh id per subscribe (`ibkr/id_manager.py:13-17`), starting at 1 —
so reqIds **13, 121, 140, 141** are app-issued depth request ids.

- The heatmap feed is **default ON** (`ui/chart_panel.py:370` `_depth_enabled_ui = True`; confirmed by
  `docs/requirements/requirements.md:699-700`), and the primary session subscribes it on every bind
  (`ui/main_window.py:960-963`). The feed is **refcounted, one per symbol** (`ibkr/market_depth.py:50-67`),
  so each symbol load / reconnect opens one new request. Four ids spread over ~7 minutes
  (1792086323385 → 1792086753374) is consistent with **four symbol loads or reconnects**, not with four
  simultaneous feeds.
- Budgets were **not** the cause: `DEPTH_FEED_CAP = 60` (`ui/main_window.py:99`) and
  `MD_LINE_CAP = 100` (`services/md_line_guard.py:16`). Neither guard fires for four feeds.
  (IBKR's own TWS cap is 3 *distinct* depth requests, error 309 — also not what the log shows.)

## 3. What error 2152 is — and why the GUI disagrees with the API

**IBKR-side facts (asserted from IBKR documentation / third-party reports — NOT verifiable in this repo):**

- IBKR's own error table labels **2152 = "Market depth smart depth exchanges."** — i.e. it is the
  *smart-depth* exchange-entitlement report. It is in the informational/warning band (2000+), the same
  band as `2104`/`2158`.
- `isSmartDepth` semantics (IBKR "Request Market Depth" doc): *"Supplying true will return data identical
  to the TWS Book Trader while False returns direct routed data similar to the TWS Market Depth tool."*
- Smart Depth (IBKR, 2019): *"aggregated depth of market (DOM) quotes from the level 1 and level 2 feeds
  **to which a user has subscribed**, instead of requiring the API client to make reqMktDepth requests to
  each exchange individually."*
- IBKR requires **additional / "off-platform" (EDS-style) subscriptions** to receive some venues' depth
  through the API that the TWS GUI shows with the ordinary subscription (documented explicitly for
  NASDAQ: without the "NASDAQ TotalView-OpenView EDS" subscription, "NASDAQ data will not be available
  whatsoever through the API").

**Why the GUI shows L2 but the API returns 2152 — the discrepancy the owner is asking about:**

The GUI and the API are not asking IBKR the same question, so "it works in TWS" is not evidence the API
is entitled:

1. **Smart depth only aggregates the venues you're entitled to, and 2152 *reports the gaps*.** TWS's own
   Book Trader / Market Depth windows render from that same entitled subset; the GUI does not raise the
   missing-venue shortfall as an error, whereas the API surface emits 2152 to name them.
2. **The log itself shows the split.** The message names only five venues as missing —
   `Need additional market data permissions - Depth: BATS; NASDAQ; ARCA; BEX; NYSE;` — while the earlier
   clause lists the venues the account *does* reach (`Depth: IEX; Top: BYX; PEARL; AMEX; T24X; MEMX;
   OVERNIGHT; EDGEA; TXSE; CHX; IBEOS; NYSENAT; PSX; LTSE; ISE; DRCTEDGE;`). The account has *some* US
   depth permission and lacks the big five **for API/off-platform use**.
3. **GUI ≠ API entitlement in IBKR's model.** For at least NASDAQ, IBKR requires a separate off-platform
   (EDS) subscription for API depth that the desktop app does not need. So a working TWS L2 window is
   fully consistent with an API that lacks those venues.

I could not verify locally *which* TWS window the owner looked at (Book Trader = SMART-aggregated vs
Market Depth = direct-routed) nor the exact IBKR message grammar; the venue grouping in (2) is my reading
of the log text and is **unverified**.

## 4. What the app does on 2152 (verified from the repo)

- `IBClient.error` classifies 2152 as `'warning'` (`ibkr/error_codes.py:22`) and, being non-`'info'`,
  emits `error_msg` (`ibkr/client.py:228-245`). **Not swallowed.**
- `MainWindow._on_error` routes it by reqId (`ui/main_window.py:1650-1690`):
  - heatmap/shared depth reqId → `TickerSession.on_depth_error` (`ui/ticker_session.py:786-798`), which
    sets state **`unavailable`** (only `354` maps to `no_entitlement`) and **cancels** the feed; the
    heatmap overlay then shows **"Depth unavailable"** (`ui/chart_panel.py:938-940`) and the status bar
    shows `Depth [2152]: <msg>` (`ui/main_window.py:1668-1670`).
  - DOM ladder reqId → status bar only, `"DOM depth [2152]: <msg> — depth subscription required."`
    (`ui/main_window.py:1677-1682`); no cancel.
- So 2152 **repeats once per request** (it is per-reqId) and, on the heatmap path, **tears the feed down**
  and shows "Depth unavailable".

Note: the `ERROR <reqId> <errorTime> <errorCode> <msg>` lines in the log carry an `errorTime` field that
the app's own handler signature `(reqId, errorCode, errorString)` does not; they are ibapi/TWS-level
(no `logging.basicConfig` exists in this repo). The same error still reaches `_on_error` via the signal.

## 5. Verdict

- **Root cause = IBKR account entitlement, i.e. configuration, not a repo defect.** The app cannot fix a
  2152 by changing code; requesting SMART depth on a `SMART` contract is the *correct* way to ask for an
  aggregated book, and it is exactly why IBKR answers with a smart-depth permission report.
- The owner's "it works in TWS" is expected to coexist with API 2152 (Section 3).
- **Owner action (IBKR-side):** in IBKR Client Portal → *Settings → Market Data Subscriptions*, check for
  the API / **off-platform (EDS-style)** L2 packages for the five venues named — **BATS, NASDAQ, ARCA,
  BEX, NYSE** (e.g. NASDAQ TotalView-OpenView **EDS**, plus the NYSE/ARCA/Cboe depth packages), and
  confirm *Market Data Lines* support the number of simultaneous depth requests (IBKR: 100 lines ⇒ max 3
  distinct depth requests). Nothing in this repo will change the 2152.

## 6. The one genuine (secondary, non-causal) repo finding — proposed ESC-035

The app folds the **partial-permission notice 2152 into the same fatal treatment as 354**:
`on_depth_error` maps every non-354 code to `unavailable` and **cancels the feed**
(`ui/ticker_session.py:794-798`). But:

- `2152` is a *partial*-permission report (it lists a subset of venues as missing while implying the rest
  are reachable), whereas `354` is a hard no-entitlement. Treating them identically discards whatever
  entitled-venue book IBKR would still stream — and it blanks a **default-ON** feature for the common
  case of an account that lacks any one major venue's depth.
- The defined behaviour covers **only 354**: `docs/requirements/requirements.md:692`,
  `docs/architecture.md:2920`, `docs/plan.md:379` (AC-D37.4). **2152 has no specified behaviour.**

I could **not verify locally** whether IBKR keeps delivering the entitled-venue book after 2152 (its
"aggregated from the feeds you're subscribed to" wording implies yes; a Sierra Chart thread shows 2152
emitted while data kept flowing). Because the desired behaviour is a product decision, this is classified
as a **requirements gap**, not a code bug — the decision must land before any code change.

Proposed escalation (not written to `escalations.json` — a parallel session owns it):

```json
{
  "id": "ESC-035",
  "task_id": "P3-T37.4",
  "routed_to": "REQUIREMENTS",
  "category": "gap",
  "severity": "should-fix",
  "observed": "reqMktDepth returns IBKR error 2152 ('Market depth smart depth exchanges' — a PARTIAL venue-permission report). ui/ticker_session.py:786-798 treats every non-354 depth error as fatal: state -> 'unavailable' and the feed is cancelled, so the default-ON heatmap shows 'Depth unavailable' and discards any entitled-venue book IBKR would still stream.",
  "expected": "Only the 354 no-entitlement path is specified (requirements.md:692, architecture.md:2920, plan.md:379 / AC-D37.4). The defined behaviour for 2152 — which the app actually receives — is undefined. Decide: (a) keep streaming the entitled venues, (b) show a distinct 'partial permissions' state, or (c) keep it fatal. Then route to BUILD.",
  "suggested_direction": "If (a)/(b): add a 2152 case to on_depth_error distinct from 354, do not cancel the shared feed, and give the panel a specific label. Regression test mirroring test_ac_d37_4: session.on_depth_error(2152, 'Need additional market data permissions - Depth: BATS; ...') -> expected state, and session.depth_req_id is/is not None as decided.",
  "status": "open",
  "opened": "<UTC now, ISO8601>"
}
```

Route rationale: the ACs specify only the 354 path, so the *behaviour for 2152* is a requirements decision
first; the code change is downstream (`BUILD`). Severity `should-fix`: default-ON feature degrades to blank
whenever the account lacks *any* major-venue depth, but it is not the cause of the permission error.

## 7. Secondary observation (unverified — not escalated)

The DOM path requests **`isSmartDepth=False` on a `SMART`-exchange contract** for stocks
(`ibkr/market_depth.py:25` + `ibkr/contracts.py:187`). IBKR's docs call non-smart depth "direct routed",
and a third-party test reports **Exchange=SMART + SMART-Depth unchecked returns no data**. If that still
holds, the Active-Trader ladder may never populate for stocks independently of entitlements. I could not
verify this locally (no TWS session) and it is not the source of the 2152 (which is a *smart*-depth
message), so I am recording it as an observation only — worth a targeted manual check, not a routed finding.

---

## Verified from the repo vs IBKR-side (unverified locally)

**Verified from the repo (`file:line`):**
- Call sites / contract / numRows / `isSmartDepth`: `ibkr/market_depth.py:25, 65, 103`;
  `ibkr/contracts.py:181-187, 237, 176-177, 239-242`; `ui/ticker_session.py:725, 770`;
  `ui/main_window.py:3004, 3012`.
- Heatmap default ON: `ui/chart_panel.py:370`; `ui/main_window.py:960-963`.
- Budgets: `ui/main_window.py:99` (`DEPTH_FEED_CAP=60`), `services/md_line_guard.py:16` (`MD_LINE_CAP=100`),
  `ui/main_window.py:805-822`.
- Error routing: `ibkr/error_codes.py:22`; `ibkr/client.py:228-245`; `ui/main_window.py:1650-1690`;
  `ui/ticker_session.py:786-798`; `ui/chart_panel.py:928-940`.
- 354 is the only specified depth error: `docs/requirements/requirements.md:692`;
  `docs/architecture.md:2920`, `docs/plan.md:379`.

**IBKR-side assertions (documentation / third-party — not verifiable in this repo):**
- 2152 = "Market depth smart depth exchanges" (IBKR error-codes table).
- `isSmartDepth` True ⇔ Book Trader (aggregated) / False ⇔ Market Depth tool (direct routed); Smart Depth
  aggregates only the L1/L2 feeds the user is subscribed to.
- API vs GUI entitlement difference and the "off-platform / EDS" requirement (documented for NASDAQ).
- Whether IBKR keeps streaming entitled-venue depth after a 2152 (key to whether the Section 6 handling is
  wrong) — **unverified**.

---

# Follow-up — diagnosis of the user-visible symptom

Owner's actual question (verbatim): *"I have access to the depth map in TWS. I want to know why I can't
see it in the app — why is the error showing?"* This section diagnoses the symptom rather than asking the
owner to choose a policy.

## Plain-language answer

Your account **does** have Level-2 depth — but only on a subset of US venues (the 2152 message lists
~15: IEX, BYX, PEARL, AMEX, T24X, MEMX, OVERNIGHT, EDGEA, TXSE, CHX, IBEOS, NYSENAT, PSX, LTSE, ISE,
DRCTEDGE) and **not** on the five big ones (BATS, NASDAQ, ARCA, BEX, NYSE). TWS shows you a book because
TWS renders the venues you *are* entitled to and quietly ignores the rest. The app asks IBKR for the same
SMART-aggregated book — and IBKR answers with the **2152** notice that *names the venues it had to drop*.
The app then treats that notice as a fatal failure and **throws the feed away**, so you see "Depth
unavailable" and no book at all. There is also a second, separate reason the **ladder** in particular can
stay empty even without the 2152 (its request shape is wrong), described below.

So: *the error is showing because IBKR reports a partial-permission gap; the depth is not showing because
the app cancels the feed on that report instead of rendering the venues you do have.*

## Cause 1 — the heatmap feed is torn down on 2152 (PROVED in the repo; default-ON path)

The chain, end to end:

1. The heatmap (`DepthHeatmapItem`) is **default ON** (`ui/chart_panel.py:370` `_depth_enabled_ui = True`),
   so the primary session subscribes a depth feed on every bind (`ui/main_window.py:960-963` →
   `TickerSession.ensure_depth_subscribed`, `ui/ticker_session.py:708-739`). That opens a **SMART-aggregated**
   request: `reqMktDepth(reqId, contract, 10, True, [])` (`ibkr/market_depth.py:65`), on a `SMART` stock
   contract (`ibkr/contracts.py:181-187`).
2. The feed's reqId is registered to the session (`_register_req_id`, `ui/ticker_session.py:728`; real
   routing at `ui/main_window.py:768-770`), and the session state is set to `"live"`
   (`ui/ticker_session.py:736`).
3. IBKR emits **2152** on that reqId. `IBClient.error` classifies it `'warning'` and emits `error_msg`
   (`ibkr/error_codes.py:22`; `ibkr/client.py:228-245`). `MainWindow._on_error` sees
   `reqId == session.depth_req_id` and calls `session.on_depth_error(2152, …)`
   (`ui/main_window.py:1664-1671`).
4. `on_depth_error` maps **every** code ≠ 354 to `"unavailable"` and calls `self._cancel_depth()`
   (`ui/ticker_session.py:786-798`). `_cancel_depth` unregisters the reqId, unsubscribes the sub-manager,
   and releases the **shared** feed (`ui/ticker_session.py:748-759` → `ibkr/market_depth.py::release_shared`
   `:69-81`).
5. The heatmap overlay then reads **"Depth unavailable"** (`ui/chart_panel.py:938-940`); the status bar shows
   `Depth [2152]: <msg>` (`ui/main_window.py:1668-1670`).

**Offscreen proof** (reproduced against the shipped code path):

```
after ensure_depth_subscribed: state='live'   req_id=4  active_feeds=1
on_depth_error(2152, "Need additional market data permissions - Depth: BATS; NASDAQ; ARCA; BEX; NYSE;")
   -> state='unavailable'  req_id=None  cancelled=True  active_feeds=0
heatmap panel state='unavailable' -> text='Depth unavailable' visible=True
```

So on the current code **no depth can render**: the feed is torn down before any book row could be applied.
This is exactly what the owner sees. (For contrast the 354 path behaves the same way — see
`tests/test_d37_microstructure.py::test_ac_d37_4_error_354_gives_explicit_state`.)

**What the owner sees per pane, on current code:**
- **Heatmap** (default ON): "Depth unavailable" centred on the plot, status bar `Depth [2152]: …` for 8 s,
  nothing else. Every symbol load/reconnect re-subscribes and re-fails, hence the **four** distinct reqIds
  in the log.
- **Active Trader ladder / DOM** (default OFF, `ui/main_window.py:252` `dom_btn.setChecked(False)`): the
  ladder renders whatever is in its snapshot; with no depth rows it is an empty ladder. If a 2152 lands on
  the DOM reqId it only shows the status-bar line `DOM depth [2152]: … — depth subscription required.`
  (`ui/main_window.py:1677-1682`) and does **not** cancel — but it still has no rows to render (see Cause 2).

## Cause 2 — the ladder's request shape is incoherent (PROVED in repo; consequence INFERRED / IBKR-side)

Independent of 2152, the ladder may never receive rows:

- `MarketDepthManager.subscribe` issues `reqMktDepth(req_id, contract, num_levels, False, [])` —
  **`isSmartDepth=False`** (`ibkr/market_depth.py:22-28`, the `:25` call).
- The contract for a stock is **`exchange="SMART"`** (`ibkr/contracts.py:181-187`, selected by
  `get_contract_for_symbol` `:237`), and `MainWindow._subscribe_dom` passes it straight through
  (`ui/main_window.py:2995-3019`).
- Offset proved on this tree:
  `LADDER (market_depth.subscribe) -> ('reqMktDepth', 1, 'SMART', 'STK', 10, False)`
  vs `HEATMAP (subscribe_shared)   -> ('reqMktDepth', 2, 'SMART', 'STK', 10, True)`.

IBKR's documentation defines `isSmartDepth=False` as **"direct routed data similar to the TWS Market Depth
tool"** and `updateMktDepth` as "used for direct routed requests only" — i.e. a non-smart request is meant
to name a **concrete venue**, not `SMART`. A third-party reproduction reports that `Exchange=SMART` with the
SMART-Depth box **unchecked returns no data** (Sierra Chart support thread 55478). **I could not verify this
against live IBKR here**, so the *repo-side* fact is "the request pairs a SMART contract with the non-smart
flag"; the *consequence* ("therefore no book") is an IBKR-side inference, not a local proof.

If it holds, this is a **second, independent bug with the same visible symptom** — the ladder would be empty
even with no 2152. Note the ladder feed is only subscribed once the user turns **DOM** on, so it is not the
cause of the default-ON heatmap being blank.

## Does the app request the venue the owner actually has?

No — and it cannot, by design. The heatmap deliberately asks for **SMART aggregation** (`isSmartDepth=True`),
which is the *same* thing TWS's Book Trader uses (IBKR: "Supplying true will return data identical to the
TWS Book Trader"). IBKR then aggregates only the venues the account is subscribed to and reports the rest via
2152. So the app is asking for the right *thing*; the failure is entirely (a) the app discards the report's
feed, and (b) the ladder asks for the wrong *mode*. The app never needs to name a venue for the heatmap path —
that is what smart depth is for.

## Ranked changes

| # | Change | Where | Sufficient alone? |
|---|---|---|---|
| 1 | **Do not tear down the feed on 2152** (keep rendering the entitled subset; surface the notice non-fatally) | `ui/ticker_session.py:786-798` (`on_depth_error`) | **Yes — for the default-ON heatmap**, i.e. it makes the app show what TWS shows. This is ESC-035/Q46 (owner decision). |
| 2 | **Fix the ladder's request shape** (`SMART`+`isSmartDepth=False` → coherent) | `ibkr/market_depth.py:25` (+ `ibkr/contracts.py:187`) | Only if the user wants the **ladder**; does nothing for the heatmap. This is ESC-039 (new). |

Change **1 alone** addresses the symptom the owner described (seeing depth in the app). Change 2 is needed
only for the separate Active-Trader ladder.

## Proved vs inferred vs unverifiable

- **Proved in the repo (`file:line`):** both request shapes (ladder `SMART/False`, heatmap `SMART/True`);
  the default-ON heatmap; the 2152 → `unavailable` + `_cancel_depth()` teardown with `active_feeds → 0`;
  the panel text "Depth unavailable"; the 354 vs 2152 branch; the DOM-default-OFF; `classify_error(2152)='warning'`.
- **Inferred (IBKR-side, not locally verifiable):** that IBKR keeps streaming the entitled-venue smart book
  after a 2152 (the pivot for change 1); that `SMART`+`isSmartDepth=False` returns no depth for stocks (the
  basis for cause 2).
- **Verified IBKR-side (documentation):** 2152 = "Market depth smart depth exchanges"; `isSmartDepth`
  True ⇔ Book Trader / False ⇔ Market Depth tool (direct routed); smart depth aggregates "the level 1 and
  level 2 feeds to which a user has subscribed".

## Routing

- **Cause 1** is already covered by **ESC-035 / Q46** (2152 behaviour undefined; owner decision pending). **Not duplicated.**
- **Cause 2** is a **distinct defect** (the ladder request shape) not covered by any existing escalation →
  raised as **ESC-039** (`routed_to: BUILD`, `category: bug`, `severity: should-fix`), with a regression test.
