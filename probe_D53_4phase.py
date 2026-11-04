"""probe_D53_4phase.py — "57-minute repro" (bounded, phase-logged).

Re-runs the 4 cancelled tests against the live TWS after the P14 fix:
  1. Connect + first load (prime + wave chunks issued).
  2. Wait for both chunk ENDs (early-exit when both complete).
  3. Deliberate same-triple reload (~RELOAD_AT_S): coalesce vs cancel+resume.
  4. Drain to wave-complete (normal) or watchdog strand-finalization.

Every phase writes its OWN log plus one combined trace; any silence/drop is
stamped with the wall-clock instant it was observed. Read-only against TWS
(no orders — order-shaped calls are guarded and counted); the app uses a
disposable SQLite DB outside the repository.

Hard bounds (no manual kill ever needed):
  GLOBAL_DEADLINE_S caps the whole run; each phase has its own ceiling.
  On expiry the probe prints a phase-stamped verdict and exits non-zero.

Usage:
  .venv/bin/python -u probe_D53_4phase.py  # needs TWS on 127.0.0.1:7496
Logs:
  /tmp/d53_4phase/P1_connect_load.log ... P4_drain.log, combined.log, VERDICT.txt
"""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
import traceback

# --------------------------------------------------------------------------
# Scenario constants (edit one place; everything else derives from these).
# --------------------------------------------------------------------------
SYMBOL = "SPY"
TIMEFRAME = "1 min"
EXT_HOURS = True
RELOAD_AT_S = 60.0
GLOBAL_DEADLINE_S = 600.0  # hard self-terminate ceiling for the whole run
PHASE2_CEIL_S = 180.0      # wait for both chunk ENDs
PHASE4_CEIL_S = 300.0      # drain to wave-complete / strand-finalization
CONNECT_CEIL_S = 30.0

LOGDIR = "/tmp/d53_4phase"

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_db = tempfile.NamedTemporaryFile(prefix="d53_4phase_", suffix=".db", delete=False)
_db.close()
os.environ["DB_PATH"] = _db.name

from PyQt6.QtCore import QEventLoop  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

APP = QApplication.instance() or QApplication(["d53_4phase"])

T0 = time.monotonic()


def ts() -> str:
    return f"{time.monotonic() - T0:7.1f}s"


def global_expired() -> bool:
    return (time.monotonic() - T0) >= GLOBAL_DEADLINE_S


class PhaseLog:
    """One log file per test phase + mirror into the combined trace."""

    def __init__(self, name: str):
        os.makedirs(LOGDIR, exist_ok=True)
        self.path = os.path.join(LOGDIR, name)
        self.combined = os.path.join(LOGDIR, "combined.log")
        self.fh = open(self.path, "w")
        self.cf = open(self.combined, "a")
        self.write(f"--- {name} opened at {ts()} (run elapsed) ---")

    def write(self, line: str) -> None:
        stamped = f"[{ts()}] {line}"
        self.fh.write(stamped + "\n")
        self.fh.flush()
        self.cf.write(stamped + "\n")
        self.cf.flush()
        print("  " + stamped, flush=True)

    def drop(self, what: str) -> None:
        self.write(f"DROP: {what}")

    def boundary(self, what: str) -> None:
        self.write(f"BOUNDARY: {what}")

    def heartbeat(self, sess, counts: dict, wave_reqs: list, label: str) -> None:
        """Periodic still-alive snapshot inside long waits — proves the pump
        loop is iterating (not wedged in one processEvents call) and shows
        exactly what the wave looks like at this instant."""
        try:
            inflight = sorted(sess._history_req_ids) if sess is not None else []
            q = len(sess._wave_plan_queue) if sess is not None else -1
            gen = sess._history_generation if sess is not None else -1
            wts = getattr(sess, "_wave_start_ts", None)
            el = (time.time() - wts) if wts else -1.0
        except Exception as e:
            self.write(f"HEARTBEAT {label}: session inspect failed: {e!r}")
            return
        got = ", ".join(f"{r}:{counts.get(r, 0)}" for r in wave_reqs) or "-"
        self.write(f"HEARTBEAT {label}: inflight={inflight} queue={q} gen={gen} "
                   f"wave_elapsed={el:.1f}s bars={{{got}}}")

    def close(self) -> None:
        try:
            self.write(f"--- closed at {ts()} ---")
            self.fh.close()
        finally:
            pass  # combined stays open for the next phase


_DEADLINE_TRIPPED = False


def mark(line: str) -> None:
    """Direct append to combined.log from outside any PhaseLog (e.g. pump)."""
    try:
        with open(os.path.join(LOGDIR, "combined.log"), "a") as fh:
            fh.write(f"[{ts()}] {line}\n")
    except Exception:
        pass
    print("  [" + ts() + "] " + line, flush=True)


def pump(ms: float, ctx: str = "") -> None:
    global _DEADLINE_TRIPPED
    end = time.monotonic() + ms / 1000.0
    while time.monotonic() < end:
        APP.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        time.sleep(0.01)
        if global_expired():
            if not _DEADLINE_TRIPPED:
                _DEADLINE_TRIPPED = True
                mark(f"DEADLINE-TRIP: global {GLOBAL_DEADLINE_S:.0f}s ceiling "
                     f"reached during {ctx or 'pump'} — all remaining waits abort")
            return


def verdict(text: str, code: int) -> int:
    with open(os.path.join(LOGDIR, "VERDICT.txt"), "w") as fh:
        fh.write(f"[{ts()}] {text}\n")
    print(f"  VERDICT [{ts()}]: {text}", flush=True)
    return code


def main() -> int:
    os.makedirs(LOGDIR, exist_ok=True)
    open(os.path.join(LOGDIR, "combined.log"), "w").write("")
    print(f"  probe_D53_4phase: {SYMBOL} / {TIMEFRAME} / ext={EXT_HOURS} "
          f"(db={_db.name})", flush=True)

    from data.bar_cache import BarCache  # noqa: E402
    from ui.main_window import MainWindow  # noqa: E402

    win = MainWindow()
    win.show()
    order_hits: list = []
    for meth in ("placeOrder", "cancelOrder", "reqGlobalCancel", "exerciseOptions"):
        for obj in (getattr(win, "ib_client", None), getattr(win, "md_manager", None)):
            if obj is not None and hasattr(obj, meth):
                real = getattr(obj, meth)

                def _guard(*a, _m=meth, _r=real, **k):
                    order_hits.append(_m)
                    return _r(*a, **k)

                setattr(obj, meth, _guard)

    # ------------------------------------------------ Phase 1: connect + load
    plog = PhaseLog("P1_connect_load.log")
    end = time.monotonic() + CONNECT_CEIL_S
    last_hb = time.monotonic()
    while not getattr(win, "_ibkr_connected", False) and time.monotonic() < end:
        pump(200, ctx="P1 connect wait")
        if time.monotonic() - last_hb >= 5.0:
            last_hb = time.monotonic()
            plog.write(f"HEARTBEAT P1-connect: connected={win._ibkr_connected} "
                       f"elapsed={time.monotonic()-T0:.1f}s")
    plog.write(f"connected={win._ibkr_connected}")
    if not getattr(win, "_ibkr_connected", False):
        plog.drop("no TWS connection within CONNECT_CEIL_S")
        plog.close()
        return verdict("P1 FAIL: no TWS connection", 2)
    if order_hits:
        plog.drop(f"order-shaped calls observed: {order_hits}")

    mdm = win.md_manager
    real_issue = mdm.req_historical_data
    real_cancel = mdm.cancel_historical_data
    events: list = []
    wave_reqs: list = []
    prime_reqs: list = []

    def spy_issue(contract, timeframe="5 mins", endDateTime="", whatToShow="TRACES",
                  useRTH=1, extended_hours=False, bar_size=None, duration=None):
        try:
            rid = real_issue(contract, timeframe, endDateTime, whatToShow,
                             useRTH, extended_hours, bar_size, duration)
        except Exception as e:  # pacing deferrals surface here
            events.append(f"ISSUE-RAISED {type(e).__name__}: {e}")
            plog.write(f"ISSUE-RAISED {type(e).__name__}: {e}")
            raise
        is_prime = (bar_size or "") == "5 secs"
        (prime_reqs if is_prime else wave_reqs).append(rid)
        events.append(f"ISSUE req={rid} tf={timeframe} end={endDateTime!r} "
                      f"dur={duration!r} bar={bar_size!r} useRTH={useRTH} ext={extended_hours}")
        plog.write(events[-1])
        return rid

    def spy_cancel(req_id):
        events.append(f"CANCEL req={req_id}")
        plog.write(events[-1])
        return real_cancel(req_id)

    mdm.req_historical_data = spy_issue
    mdm.cancel_historical_data = spy_cancel

    counts: dict = {}
    ends: dict = {}
    bridge = win.ib_client.bridge

    def on_bar(req_id, bar):
        counts[req_id] = counts.get(req_id, 0) + 1

    def on_end(req_id):
        ends[req_id] = time.monotonic() - T0
        events.append(f"END req={req_id} bars={counts.get(req_id, 0)}")
        plog.write(events[-1])

    def on_err(req_id, code, msg):
        events.append(f"ERR req={req_id} code={code} {str(msg)[:90]}")
        plog.write(events[-1])

    bridge.historical_bar.connect(on_bar)
    bridge.historical_data_end.connect(on_end)
    bridge.error_msg.connect(on_err)

    win.load_chart(SYMBOL, TIMEFRAME, True)
    pump(1000)
    sess = win._sessions.get(SYMBOL)
    if sess is None:
        plog.drop("no session after load_chart")
        plog.close()
        return verdict("P1 FAIL: no session", 2)
    plog.write(f"queue_depth={len(sess._wave_plan_queue)} "
               f"inflight={sorted(sess._history_req_ids)} gen={sess._history_generation}")
    try:
        for p in list(sess._wave_plan_queue)[:6]:
            plog.write(f"PLAN end={p.endDateTime!r} dur={p.duration!r} bar={p.bar_size!r}")
    except Exception as e:
        plog.write(f"plan-dump failed: {e!r}")
    try:
        from ibkr.pacing import pacing_manager
        plog.write(f"pacing slots held: {len(pacing_manager._hist_times)}")
    except Exception as e:
        plog.write(f"pacing inspect failed: {e!r}")
    plog.write(f"cache now: {len(BarCache.get_bars(SYMBOL, TIMEFRAME, ext_hours=EXT_HOURS))} bars")
    try:
        bound = sess._history_wave_watchdog_bound_ms()
        plog.write(f"watchdog bound armed ~{bound}ms; _wave_start_ts={sess._wave_start_ts}")
    except Exception as e:
        plog.write(f"watchdog bound inspect failed: {e!r}")
    plog.boundary(f"P1 done: issued wave={wave_reqs} prime={prime_reqs}")
    plog.close()

    # ------------------------------------------------ Phase 2: wait both ENDs
    plog = PhaseLog("P2_chunk_ends.log")
    if not wave_reqs:
        plog.drop("no wave requests were issued in P1 — nothing to wait for")
    deadline = time.monotonic() + PHASE2_CEIL_S
    done_reqs: set = set()
    last_hb = time.monotonic()
    while time.monotonic() < deadline and not global_expired():
        pump(500, ctx="P2 chunk-END wait")
        if time.monotonic() - last_hb >= 10.0:
            last_hb = time.monotonic()
            plog.heartbeat(sess, counts, wave_reqs, "P2-wait")
        for r in wave_reqs:
            if r in ends and r not in done_reqs:
                done_reqs.add(r)
                plog.write(f"chunk END req={r} at +{ends[r]:.1f}s "
                           f"bars={counts.get(r, 0)}")
        if wave_reqs and len(done_reqs) == len(wave_reqs):
            break
    for r in wave_reqs:
        if r not in ends:
            plog.drop(f"req={r} silent: {counts.get(r, 0)} bars, no END after "
                      f"{PHASE2_CEIL_S:.0f}s wait")
        else:
            plog.write(f"req={r} completed: {counts.get(r, 0)} bars")
    plog.write(f"cache now: {len(BarCache.get_bars(SYMBOL, TIMEFRAME, ext_hours=EXT_HOURS))} bars")
    both_done = bool(wave_reqs) and all(r in ends for r in wave_reqs)
    plog.write(f"both wave ENDs observed: {both_done}")
    plog.close()

    # ------------------------------------------------ Phase 3: reload @ ~60 s
    plog = PhaseLog("P3_reload.log")
    wait_until = T0 + RELOAD_AT_S
    if time.monotonic() >= wait_until:
        plog.write(f"NOTE: P2 ran long — reloading LATE at +{time.monotonic()-T0:.1f}s "
                   f"(target was +{RELOAD_AT_S:.0f}s); coalescing verdict still valid")
    while time.monotonic() < wait_until and not global_expired():
        pump(500, ctx="P3 pre-reload hold")
    sess = win._sessions.get(SYMBOL)
    pre_inflight = sorted(sess._history_req_ids) if sess else []
    pre_queue = len(sess._wave_plan_queue) if sess else -1
    pre_gen = sess._history_generation if sess else -1
    n_issued_before = len(wave_reqs)
    plog.write(f"pre-reload inflight={pre_inflight} queue={pre_queue} gen={pre_gen} "
               f"issued_so_far={n_issued_before}")
    win.load_chart(SYMBOL, TIMEFRAME, True)
    pump(1500)
    sess = win._sessions.get(SYMBOL)
    post_inflight = sorted(sess._history_req_ids) if sess else []
    post_queue = len(sess._wave_plan_queue) if sess else -1
    post_gen = sess._history_generation if sess else -1
    new_reqs = [r for r in wave_reqs if r not in wave_reqs[:n_issued_before]]
    status = win.status_bar.currentMessage()
    plog.write(f"post-reload status={status!r}")
    plog.write(f"post-reload inflight={post_inflight} queue={post_queue} gen={post_gen}")
    if new_reqs:
        plog.write(f"reload issued {len(new_reqs)} NEW reqIds: {new_reqs} (cancel+resume path)")
    else:
        plog.write("reload issued 0 new reqIds (coalesced into running wave)")
        if post_gen != pre_gen:
            plog.drop(f"generation moved {pre_gen}->{post_gen} with no new requests")
    plog.close()

    # ------------------------------------------------ Phase 4: drain
    plog = PhaseLog("P4_drain.log")
    deadline = time.monotonic() + PHASE4_CEIL_S
    last_hb = time.monotonic()
    while time.monotonic() < deadline and not global_expired():
        pump(1000, ctx="P4 drain wait")
        if time.monotonic() - last_hb >= 10.0:
            last_hb = time.monotonic()
            s = win._sessions.get(SYMBOL)
            plog.heartbeat(s, counts, wave_reqs, "P4-drain")
        s = win._sessions.get(SYMBOL)
        if s is not None and not s._wave_plan_queue and not s._history_req_ids:
            break
    s = win._sessions.get(SYMBOL)
    empty = s is not None and not s._wave_plan_queue and not s._history_req_ids
    n_final = len(BarCache.get_bars(SYMBOL, TIMEFRAME, ext_hours=EXT_HOURS))
    plog.write(f"drained (queue+inflight empty): {empty}")
    plog.write(f"final cached bars: {n_final}")
    plog.write(f"wave reqIds: {wave_reqs} prime reqIds: {prime_reqs}")
    for r in wave_reqs:
        plog.write(f"req={r}: bars={counts.get(r, 0)} "
                   f"end_at={'+' + format(ends[r], '.1f') + 's' if r in ends else 'NEVER'}")
    shortfall = ""
    try:
        shortfall = win.status_bar.currentMessage()
    except Exception:
        pass
    plog.write(f"final status line: {shortfall!r}")
    if order_hits:
        plog.drop(f"order-shaped calls during run: {order_hits}")
    plog.close()

    try:
        win.close()
    except Exception:
        traceback.print_exc()

    if global_expired():
        return verdict("GLOBAL DEADLINE EXCEEDED — see per-phase logs for last-known state", 3)
    if not empty:
        return verdict("P4 INCOMPLETE: wave did not drain within PHASE4_CEIL_S", 1)
    if both_done:
        return verdict(f"ALL GREEN: both chunk ENDs + clean drain, {n_final} cached bars", 0)
    return verdict("WATCHDOG PATH: drained via strand-finalization; see P2 drops + P4 shortfall", 0)


if __name__ == "__main__":
    code = main()
    print(f"  exit={code}", flush=True)
    sys.exit(code)
