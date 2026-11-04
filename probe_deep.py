"""Deep live trace: log every historical request's args and every bridge callback."""

from __future__ import annotations

import os
import tempfile
import threading
import time

_db = tempfile.NamedTemporaryFile(prefix="livedeep_", suffix=".db", delete=False)
_db.close()
os.environ["DB_PATH"] = _db.name
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEventLoop  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

APP = QApplication.instance() or QApplication(["livedeep"])


def pump(ms):
    end = time.monotonic() + ms / 1000.0
    while time.monotonic() < end:
        APP.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        time.sleep(0.01)


def main() -> int:
    from ibkr.pacing import pacing_manager  # noqa: E402
    from data.bar_cache import BarCache  # noqa: E402
    from ui.main_window import MainWindow  # noqa: E402

    t0 = time.monotonic()
    log = []

    def ts():
        return f"{time.monotonic()-t0:6.1f}s"

    win = MainWindow()
    win.show()

    end = time.monotonic() + 30
    while not win._ibkr_connected and time.monotonic() < end:
        pump(200)
    print(f"  [{ts()}] connected={win._ibkr_connected}")
    if not win._ibkr_connected:
        return 2

    mdm = win.md_manager
    real_issue = mdm.req_historical_data
    real_cancel = mdm.cancel_historical_data
    wave_reqs: list = []

    def spy_issue(contract, timeframe="5 mins", endDateTime="", whatToShow="TRADES",
                  useRTH=1, extended_hours=False, bar_size=None, duration=None):
        try:
            rid = orig_issue(contract, timeframe, endDateTime, whatToShow,
                             useRTH, extended_hours, bar_size, duration)
            if (bar_size or "") != "5 secs":
                wave_reqs.append(rid)
            log.append(f"[{ts()}] ISSUE req={rid} tf={timeframe} end={endDateTime!r} "
                       f"dur={duration!r} bar={bar_size!r}")
            return rid
        except Exception as e:
            log.append(f"[{ts()}] ISSUE-RAISED {type(e).__name__}: {e}")
            raise

    def spy_cancel(req_id):
        log.append(f"[{ts()}] CANCEL req={req_id}")
        return real_cancel(req_id)

    mdm.req_historical_data = spy_issue
    mdm.cancel_historical_data = spy_cancel

    b = win.ib_client.bridge
    counts: dict = {}
    b.historical_bar.connect(
        lambda req_id, bar: counts.__setitem__(req_id, counts.get(req_id, 0) + 1))
    b.historical_data_end.connect(
        lambda req_id: log.append(f"[{ts()}] END req={req_id} bars={counts.get(req_id,0)}"))
    def on_err(req_id, code, msg):
        log.append(f"[{ts()}] ERR req={req_id} code={code} {str(msg)[:80]}")
    b.error_msg.connect(on_err)

    win.load_chart("AAPL", "1 min")
    pump(1000)
    sess = win._sessions.get("AAPL")
    if sess is not None:
        log.append(f"[{ts()}] queue_depth={len(sess._wave_plan_queue)} "
                   f"inflight={sorted(sess._history_req_ids)} "
                   f"gen={sess._history_generation}")
        try:
            plans = list(sess._wave_plan_queue)
            for p in plans[:6]:
                log.append(f"[{ts()}] PLAN end={p.endDateTime!r} dur={p.duration!r} bar={p.bar_size!r}")
            if len(plans) > 6:
                log.append(f"[{ts()}] ... +{len(plans)-6} more plans")
        except Exception as e:
            log.append(f"[{ts()}] plan-dump failed: {e!r}")

    # wait for ALL wave chunks (not the prime) — up to 300 s
    wave_done: dict = {}
    wave_end_seen = {r: threading.Event() for r in []}

    def mark_wave_end(req_id):
        if req_id in wave_reqs:
            wave_end_seen.setdefault(req_id, threading.Event()).set()

    b.historical_data_end.connect(mark_wave_end)
    end = time.monotonic() + 300
    while time.monotonic() < end:
        pump(500)
        if wave_reqs and all(
                wave_end_seen.get(r, threading.Event()).is_set() for r in wave_reqs):
            break
    for r in wave_reqs:
        log.append(f"[{ts()}] wave req={r} bars={counts.get(r, 0)} "
                   f"ended={bool(wave_end_seen.get(r) and wave_end_seen[r].is_set())}")
    log.append(f"[{ts()}] cached bars now: "
               f"{len(BarCache.get_bars('AAPL', '1 min', ext_hours=False))}")

    # deliberate same-triple reload at ~60 s in: coalesce or cancel+resume?
    if sess is not None:
        log.append(f"[{ts()}] pre-reload inflight={sorted(sess._history_req_ids)} "
                   f"queue={len(sess._wave_plan_queue)}")
    win.load_chart("AAPL", "1 min")
    pump(1500)
    log.append(f"[{ts()}] post-reload status={win.status_bar.currentMessage()!r}")
    if sess is not None:
        log.append(f"[{ts()}] post-reload inflight={sorted(sess._history_req_ids)} "
                   f"queue={len(sess._wave_plan_queue)}")
    # drain to completion (bounded)
    end = time.monotonic() + 240
    while time.monotonic() < end:
        pump(1000)
        s = win._sessions.get("AAPL")
        if s is not None and not s._wave_plan_queue and not s._history_req_ids:
            break
    log.append(f"[{ts()}] final cached bars: {len(_BC.get_bars('AAPL', '1 min', ext_hours=False))}")

    print("  --- trace ---")
    for line in log:
        print("  " + line)
    win.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
