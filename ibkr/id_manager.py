import threading

class IdManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._next_id = 1

    def set_next_valid_id(self, order_id: int):
        with self._lock:
            if order_id > self._next_id:
                self._next_id = order_id

    def get_id(self) -> int:
        with self._lock:
            current_id = self._next_id
            self._next_id += 1
            return current_id

    def release_id(self, req_id: int) -> bool:
        """Return the newest allocation to the pool (D81).

        A request whose client call raised never crossed the wire, so its
        reqId may be handed out again and the id sequence has no
        failure-shaped gap. Only the most recent allocation can be rolled
        back: an older id may still be live on the wire, and releasing it
        would hand out an id another request owns. Returns True when the
        rollback happened; False (and no change) otherwise. The lock covers
        both the check and the write.
        """
        with self._lock:
            if self._next_id - 1 == req_id:
                self._next_id = req_id
                return True
            return False

# Global singleton
id_manager = IdManager()
