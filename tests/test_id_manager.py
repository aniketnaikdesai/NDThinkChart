"""Tests for ibkr/id_manager.py — ID allocation semantics.

D26.2: bracket orders consume three order IDs; they must be reserved as a
contiguous block so no later get_id() reissues a live order ID.
"""

from ibkr.id_manager import IdManager


def test_reserve_returns_contiguous_block():
    mgr = IdManager()
    first = mgr.reserve(3)
    assert isinstance(first, int)
    # The block is [first, first+1, first+2]; the next allocation starts after it.
    assert mgr.get_id() == first + 3


def test_reserve_never_overlaps_later_allocations():
    # AC-D26.2: distinct, sequential, never reissued across placements.
    mgr = IdManager()
    seen = set()
    for _ in range(5):
        first = mgr.reserve(3)
        block = {first, first + 1, first + 2}
        assert not (block & seen), f"reserved block {block} overlaps {seen}"
        seen |= block
        # Interleave single allocations (market-data reqIds share the counter).
        seen.add(mgr.get_id())
    assert len(seen) == 5 * 4


def test_reserve_one_matches_get_id_semantics():
    mgr = IdManager()
    a = mgr.reserve(1)
    b = mgr.get_id()
    assert b == a + 1


def test_set_next_valid_id_still_monotonic_with_reserve():
    mgr = IdManager()
    first = mgr.reserve(3)
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


def test_reserve_rejects_non_positive():
    import pytest

    mgr = IdManager()
    for bad in (0, -1, -100):
        with pytest.raises(ValueError):
            mgr.reserve(bad)
    # The failed reservations must not consume IDs.
    assert mgr.get_id() == 1


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
        first = mgr.reserve(3)
        local.update({first, first + 1, first + 2})
        with lock:
            assert not (local & seen), "duplicate id across threads"
            seen.update(local)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert all(not t.is_alive() for t in threads)
    assert len(seen) == 8 * 203
