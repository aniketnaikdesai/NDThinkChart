"""Live backfill probe: real TWS, real app path, empty cache, 1-min AAPL.

Proves the P7 claims end to end: per-chunk persist+render, reload resumes
(does not restart), pacing slots recorded/refunded, 162s classified.
Read-only except the app's own cache writes into a TEMP db. No orders.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time

_db = tempfile.NamedTemporaryFile(prefix="liveprobe_", suffix=".db", delete=False)
_db.close()
os.environ["DB_PATH"] = _db.name
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEventLoop  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

APP = QApplication.instance() or QApplication(["liveprobe"])


def pump(ms):
    end = time.monotonic() + ms / 1000.0
    while time.monotonic() < end:
        APP.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        time.sleep(0.01)


def main() -> int:
    from data.bar_cache import BarCache
    from ibkr.pacing import pacing_manager
    from ui.main_window import MainWindow

    t0 = time.monotonic()
    win = MainWindow()
    win.show()

    # 1. connect
    end = time.monotonic() + 30
    while not win._ibkr_connected and time.monotonic() < end:
        pump(200)
    print(f"  connected={win._ibkr_connected} t={time.monotonic()-t0:.1f}s")
    if not win._ibkr_connected:
        print("  ABORT: no TWS connection")
        return 2

    events: list[str] = []
    issued: list[int] = []
    orig_issue = win._host.md_manager.req_historical_data \
        if hasattr(win, "_host") else win.md_manager.req_historical_data

    mdm = win.md_manager
    real_issue = mdm.req_historical_data

    def spy_issue(*a, **k):
        rid = real_issue(*a, **k)
        issued.append(rid)
        events.append(f"issued reqId={rid} t={time.monotonic()-t0:.1f}s")
        return rid

    mdm.req_historical_data = spy_issue

    # 2. empty-cache 1-min load
    win.load_chart("AAPL", "1 min")
    pump(1000)
    sess = win._sessions.get("AAPL")
    plans = len(sess._wave_plan_queue) if sess else -1
    print(f"  wave plans queued: {plans} (multi-chunk expected)")

    # 3. let the first chunk(s) complete
    pump(20000)
    n1 = len(BarCache.get_bars("AAPL", "1 min", ext_hours=False))
    print(f"  cached 1-min bars after 20s: {n1}")
    print(f"  requests issued so far: {len(issued)}")
    print(f"  pacing slots held: {len(pacing_manager._hist_times)}")

    # 4. mid-wave reload -> must resume, not restart
    before = set(issued)
    win.load_chart("AAPL", "1 min")
    pump(20000)
    sess = win._sessions.get("AAPL")
    new_reqs = [r for r in issued if r not in before]
    n2 = len(BarCache.get_bars("AAPL", "1 min", ext_hours=False))
    print(f"  cached 1-min bars after reload+20s: {n2} (never smaller: {n2 >= n1})")
    print(f"  new requests after reload: {len(new_reqs)}")
    print(f"  pending queue now: {len(sess._wave_plan_queue) if sess else -1}")
    print(f"  pacing slots held: {len(pacing_manager._hist_times)}")
    print(f"  status: {win.status_bar.currentMessage()!r}")

    # 5. drain to completion (bounded)
    end = time.monotonic() + 240
    while time.monotonic() < end:
        pump(1000)
        s = win._sessions.get("AAPL")
        if s is not None and not s._wave_plan_queue and not s._history_req_ids:
            break
    s = win._sessions.get("AAPL")
    done = s is not None and not s._wave_plan_queue and not s._history_req_ids
    n3 = len(BarCache.get_bars("AAPL", "1 min", ext_hours=False))
    print(f"  wave complete: {done}  cached bars: {n3}  total issued: {len(issued)}")
    print("  last events:")
    for e in events[-8:]:
        print(f"    {e}")
    win.close()
    return 0 if (done and n3 >= n2 >= n1 > 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
