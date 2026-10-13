"""D38 news API client (38a.1).

Wraps the IBKR news endpoints used by the news-for-holdings digest:
``reqNewsProviders`` (entitled provider list), ``reqHistoricalNews`` (per-holding
headline backfill) and ``reqNewsArticle`` (article body on headline click).

Headline fetches are issued **strictly sequentially** (FIFO queue, one in
flight) so opening the digest can never storm the news API — the plan's
pacing requirement (38a.1). News requests are not counted against the 600s
historical budget (plan §7: "not counted unless observed limited").
"""

from collections import deque
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal

from ibkr.id_manager import id_manager

# IBKR expects "YYYYMMDD-HH:MM:SS" for historical-news bounds.
_NEWS_DT_FMT = "%Y%m%d-%H:%M:%S"


def _fmt_news_dt(dt: datetime) -> str:
    return dt.strftime(_NEWS_DT_FMT)


class NewsManager(QObject):
    """Owns all IBKR news requests for the digest. Strictly additive."""

    providers_received = pyqtSignal(list)          # [NewsProvider]
    headlines_batch = pyqtSignal(int, list, bool)  # req_id, [headline dict], has_more
    article_received = pyqtSignal(int, int, str)   # req_id, articleType, articleText

    def __init__(self, client):
        super().__init__()
        self.client = client
        self._queue: deque = deque()   # pending (con_id, provider_codes, start, end, total)
        self._in_flight: int | None = None
        self._pending_headlines: dict[int, list] = {}
        bridge = client.bridge
        bridge.news_providers.connect(self._on_providers)
        bridge.historical_news.connect(self._on_headline)
        bridge.historical_news_end.connect(self._on_headlines_end)
        bridge.news_article.connect(self._on_article)

    # ── Public API ────────────────────────────────────────────────────

    def request_providers(self) -> None:
        """Ask TWS for the API news providers this account is entitled to."""
        self.client.reqNewsProviders()

    def request_headlines(self, con_id: int, provider_codes: str,
                          start: datetime, end: datetime,
                          total_results: int = 20) -> int:
        """Queue a per-holding headline backfill. Returns the reqId.

        Requests are issued one at a time in FIFO order (38a.1). ``con_id``
        must be the IBKR contract id of the holding; ``provider_codes`` is
        the "+"-joined entitled provider codes.
        """
        req_id = id_manager.get_id()
        self._queue.append((req_id, con_id, provider_codes,
                            _fmt_news_dt(start), _fmt_news_dt(end),
                            total_results))
        self._pump()
        return req_id

    def request_article(self, provider_code: str, article_id: str) -> int:
        """Fetch one article body. Returns the reqId."""
        req_id = id_manager.get_id()
        self.client.reqNewsArticle(req_id, provider_code, article_id, [])
        return req_id

    def cancel_all(self) -> None:
        """Drop queued (not yet issued) headline requests, e.g. on digest close."""
        self._queue.clear()

    @property
    def queue_depth(self) -> int:
        """Pending + in-flight headline requests (for tests/assertions)."""
        return len(self._queue) + (1 if self._in_flight is not None else 0)

    # ── Internals ─────────────────────────────────────────────────────

    def _pump(self) -> None:
        if self._in_flight is not None or not self._queue:
            return
        req_id, con_id, provider_codes, start, end, total = self._queue.popleft()
        self._in_flight = req_id
        self._pending_headlines[req_id] = []
        self.client.reqHistoricalNews(req_id, con_id, provider_codes,
                                      start, end, total, [])

    def _on_providers(self, news_providers) -> None:
        self.providers_received.emit(list(news_providers or []))

    def _on_headline(self, req_id: int, time: str, provider_code: str,
                     article_id: str, headline: str) -> None:
        batch = self._pending_headlines.get(req_id)
        if batch is None:
            return
        batch.append({
            "time": time,
            "provider_code": provider_code,
            "article_id": article_id,
            "headline": headline,
        })

    def _on_headlines_end(self, req_id: int, has_more: bool) -> None:
        batch = self._pending_headlines.pop(req_id, [])
        if self._in_flight == req_id:
            self._in_flight = None
        self.headlines_batch.emit(req_id, batch, has_more)
        self._pump()

    def _on_article(self, req_id: int, article_type: int,
                    article_text: str) -> None:
        self.article_received.emit(req_id, article_type, article_text)
