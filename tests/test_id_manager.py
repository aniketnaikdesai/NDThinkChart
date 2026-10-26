"""Tests for ibkr/id_manager.py — ID allocation semantics.

Every ID comes from one monotonic counter: get_id() hands out the next value,
and TWS's nextValidId seeds it forward but can never move it backwards.
"""

from ibkr.id_manager import IdManager


def test_set_next_valid_id_still_monotonic():
    mgr = IdManager()
    first = mgr.get_id()
    mgr.set_next_valid_id(first + 100)
    assert mgr.get_id() == first + 100
    # A stale (lower) nextValidId must not move the counter backwards.
    mgr.set_next_valid_id(first + 2)
    assert mgr.get_id() == first + 101


def test_get_id_allocates_sequentially():
    mgr = IdManager()
    ids = [mgr.get_id() for _ in range(5)]
    assert ids == [ids[0] + i for i in range(5)]
    assert len(set(ids)) == 5


def test_set_next_valid_id_equal_is_noop():
    mgr = IdManager()
    first = mgr.get_id()
    mgr.set_next_valid_id(first + 1)  # equal to the pending next id
    assert mgr.get_id() == first + 1  # unchanged, not skipped


def test_concurrent_allocations_never_duplicate():
    import threading

    mgr = IdManager()
    seen = set()
    lock = threading.Lock()

    def worker():
        local = set()
        for _ in range(200):
            local.add(mgr.get_id())
        with lock:
            assert not (local & seen), "duplicate id across threads"
            seen.update(local)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert all(not t.is_alive() for t in threads)
    assert len(seen) == 8 * 200
