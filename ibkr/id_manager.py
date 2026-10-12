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

    def reserve(self, n: int) -> int:
        """Reserve a contiguous block of ``n`` IDs; return the first.

        D26.2: multi-leg orders (brackets) must hold all their IDs before
        transmitting, so no later ``get_id()`` can reissue a live order ID.
        """
        if n < 1:
            raise ValueError(f"reserve() requires n >= 1, got {n}")
        with self._lock:
            first_id = self._next_id
            self._next_id += n
            return first_id

# Global singleton
id_manager = IdManager()
