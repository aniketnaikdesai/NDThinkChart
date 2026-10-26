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

# Global singleton
id_manager = IdManager()
