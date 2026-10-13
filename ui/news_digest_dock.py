"""
news_digest_dock.py — D38 (38a.2): news-for-holdings digest.

A repositionable, closable QDockWidget listing recent headlines per currently
held position, grouped by holding. Refresh = backfill on open (sequential
``reqHistoricalNews`` per holding) + live push primary (generic tick "292"
via each holding's S0 subscription -> headline prepended) + 15-minute
periodic re-query backstop (only while open).

Holdings that are neither charted nor alarm-monitored get a lightweight
headless ``TickerSession`` while the digest is open (D24 headless semantics),
torn down on close. Their S0 lines count in the §7 MD-line budget via the
normal ``_md_line_count`` accounting.

Honesty states (never silently empty):
- no API news subscription -> "no news entitlement"
- zero positions -> empty state
- per-symbol headline failure -> that section shows "unavailable"
"""

from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDockWidget, QDialog, QGroupBox, QLabel, QListWidget, QListWidgetItem,
    QScrollArea, QTextBrowser, QVBoxLayout, QWidget,
)

# Backfill window / per-holding headline cap (38a.1: sequential, no storms).
_BACKFILL_DAYS = 14
_HEADLINES_PER_HOLDING = 30
_BACKSTOP_MINUTES = 15


class _ArticleDialog(QDialog):
    def __init__(self, parent, symbol: str, headline: str, body: str):
        super().__init__(parent)
        self.setWindowTitle(f"{symbol} — {headline[:60]}")
        self.resize(560, 420)
        layout = QVBoxLayout(self)
        browser = QTextBrowser(self)
        browser.setPlainText(body or "(empty article body)")
        layout.addWidget(browser)


class NewsDigestDock(QDockWidget):
    """News-for-holdings digest dock (38a.2)."""

    def __init__(self, host, parent=None):
        super().__init__("News Digest", parent)
        self._host = host  # MainWindow (duck-typed)
        self.setObjectName("NewsDigest")
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        self._req_to_symbol: dict[int, str] = {}
        self._article_to_ctx: dict[int, tuple[str, str]] = {}
        self._headless_symbols: set[str] = set()
        self._holding_sessions: dict[str, object] = {}
        self._providers: list = []
        self._open = False

        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)

        self._status = QLabel("", root)
        self._status.setWordWrap(True)
        self._status.setStyleSheet("color: #94a3b8;")
        layout.addWidget(self._status)

        self._scroll = QScrollArea(root)
        self._scroll.setWidgetResizable(True)
        self._sections_host = QWidget(self._scroll)
        self._sections_layout = QVBoxLayout(self._sections_host)
        self._sections_layout.addStretch(1)
        self._scroll.setWidget(self._sections_host)
        layout.addWidget(self._scroll)
        self.setWidget(root)

        self._backstop = QTimer(self)
        self._backstop.setInterval(_BACKSTOP_MINUTES * 60 * 1000)
        self._backstop.timeout.connect(self._on_backstop)
        # Signal wiring is deferred to first open: the dock is constructed
        # before MainWindow creates news_manager (init order).
        self._wired = False

    def _ensure_wired(self) -> None:
        if self._wired:
            return
        nm = self._host.news_manager
        nm.providers_received.connect(self._on_providers)
        nm.headlines_batch.connect(self._on_headlines_batch)
        nm.article_received.connect(self._on_article)
        self._wired = True

    # ── Open / close lifecycle ─────────────────────────────────────

    def open_digest(self) -> None:
        """(Re)open: backfill headlines for every holding."""
        self._ensure_wired()
        self._open = True
        self.setVisible(True)
        self._set_status("Loading news providers…")
        self._clear_sections()
        self._host.news_manager.request_providers()

    def close_digest(self) -> None:
        self._open = False
        self._backstop.stop()
        self._host.news_manager.cancel_all()
        self._teardown_holding_sessions()
        self.setVisible(False)

    def is_digest_open(self) -> bool:
        return self._open

    # ── Holdings ───────────────────────────────────────────────────

    def _holdings(self) -> list[tuple[str, int]]:
        """(symbol, con_id) for current positions with a usable conId."""
        try:
            from data.db import db
            rows = db.conn.execute(
                "SELECT DISTINCT symbol, con_id FROM positions "
                "WHERE con_id IS NOT NULL"
            ).fetchall()
        except Exception:
            return []
        seen: dict[str, int] = {}
        for symbol, con_id in rows:
            if symbol and con_id and symbol.upper() not in seen:
                seen[symbol.upper()] = int(con_id)
        return sorted(seen.items())

    # ── Provider / backfill flow ───────────────────────────────────

    def _on_providers(self, providers) -> None:
        if not self._open:
            return
        self._providers = [p for p in (providers or []) if p is not None]
        if not self._providers:
            # Honest no-entitlement state (AC-D38.3) — never silently empty.
            self._set_status(
                "No API news subscription — no news providers are entitled "
                "for API access on this account. (Most TWS news services are "
                "not available via the API.)"
            )
            return
        holdings = self._holdings()
        if not holdings:
            self._set_status("No holdings — nothing to digest.")
            return
        names = ", ".join(p.name or p.code for p in self._providers)
        self._set_status(f"Providers: {names}")
        self._ensure_holding_sessions([s for s, _ in holdings])
        self._backfill(holdings)

    def _backfill(self, holdings: list[tuple[str, int]]) -> None:
        codes = "+".join(p.code for p in self._providers if p.code)
        if not codes:
            return
        nm = self._host.news_manager
        end = datetime.now()
        start = end - timedelta(days=_BACKFILL_DAYS)
        for symbol, con_id in holdings:
            self._ensure_section(symbol, loading=True)
            req_id = nm.request_headlines(con_id, codes, start, end,
                                          _HEADLINES_PER_HOLDING)
            self._req_to_symbol[req_id] = symbol
        if not self._backstop.isActive():
            self._backstop.start()

    def _on_backstop(self) -> None:
        """Periodic re-query backstop (only while open)."""
        if not self._open or not self._providers:
            return
        self._backfill(self._holdings())

    def _on_headlines_batch(self, req_id: int, headlines: list,
                            has_more: bool) -> None:
        symbol = self._req_to_symbol.pop(req_id, None)
        if symbol is None or not self._open:
            return
        section = self._ensure_section(symbol)
        lst: QListWidget = section["list"]
        if not headlines:
            section["note"].setText("Headlines unavailable for this holding.")
            return
        # Backfill replaces the section (live pushes prepend on top).
        lst.clear()
        for h in headlines:
            self._add_headline_item(lst, symbol, h)

    # ── Live push (tick 292 via S0) ────────────────────────────────

    def _ensure_holding_sessions(self, symbols: list[str]) -> None:
        """Every holding gets an S0 "292" need; non-charted, unmonitored
        holdings get a lightweight headless session (plan 38a.2)."""
        host = self._host
        for symbol in symbols:
            key = symbol.upper()
            session = host.get_or_create_session(key)
            self._holding_sessions[key] = session
            if not session.views and not session.monitored:
                session.set_s0_headless(True)
                self._headless_symbols.add(key)
            session.s0_register("news", {"292"})
            session.add_news_push_listener(self._on_news_push)

    def _teardown_holding_sessions(self) -> None:
        host = self._host
        for key, session in self._holding_sessions.items():
            try:
                session.remove_news_push_listener(self._on_news_push)
                session.s0_deregister("news")
                if key in self._headless_symbols:
                    session.set_s0_headless(False)
                    if not session.views and not session.monitored:
                        host._teardown_session(key)
            except Exception:
                pass
        self._holding_sessions.clear()
        self._headless_symbols.clear()

    def _on_news_push(self, symbol: str, _ts: int, provider_code: str,
                      article_id: str, headline: str) -> None:
        """Live tick-292 headline — prepend to the holding's section."""
        if not self._open:
            return
        section = self._sections.get(symbol.upper())
        if section is None:
            section = self._ensure_section(symbol.upper())
        self._add_headline_item(
            section["list"], symbol.upper(),
            {"time": "", "provider_code": provider_code,
             "article_id": article_id, "headline": headline},
            prepend=True)

    # ── Sections UI ────────────────────────────────────────────────

    def _clear_sections(self) -> None:
        if not hasattr(self, "_sections"):
            self._sections = {}
        for key in list(self._sections):
            self._sections.pop(key)["box"].setParent(None)

    def _ensure_section(self, symbol: str, loading: bool = False) -> dict:
        if not hasattr(self, "_sections"):
            self._sections = {}
        key = symbol.upper()
        if key in self._sections:
            return self._sections[key]
        box = QGroupBox(key, self._sections_host)
        vbox = QVBoxLayout(box)
        note = QLabel("", box)
        note.setStyleSheet("color: #94a3b8; font-size: 11px;")
        note.setWordWrap(True)
        vbox.addWidget(note)
        lst = QListWidget(box)
        lst.setMaximumHeight(220)
        lst.itemClicked.connect(self._on_headline_clicked)
        vbox.addWidget(lst)
        # Insert before the stretch.
        self._sections_layout.insertWidget(
            self._sections_layout.count() - 1, box)
        section = {"box": box, "list": lst, "note": note}
        self._sections[key] = section
        if loading:
            note.setText("Loading headlines…")
        return section

    def _set_status(self, text: str) -> None:
        self._status.setText(text)
        self._status.setVisible(bool(text))

    def _add_headline_item(self, lst: QListWidget, symbol: str,
                           h: dict, prepend: bool = False) -> None:
        text = h.get("headline") or "(no headline)"
        when = h.get("time") or ""
        prov = h.get("provider_code") or ""
        label = f"{when} [{prov}] {text}".strip()
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole,
                     (symbol, h.get("provider_code") or "",
                      h.get("article_id") or "", text))
        if prepend:
            lst.insertItem(0, item)
        else:
            lst.addItem(item)

    def _on_headline_clicked(self, item: QListWidgetItem) -> None:
        ctx = item.data(Qt.ItemDataRole.UserRole)
        if not ctx:
            return
        symbol, provider_code, article_id, headline = ctx
        if not provider_code or not article_id:
            return
        req_id = self._host.news_manager.request_article(provider_code,
                                                         article_id)
        self._article_to_ctx[req_id] = (symbol, headline)

    def _on_article(self, req_id: int, _article_type: int,
                    article_text: str) -> None:
        ctx = self._article_to_ctx.pop(req_id, None)
        if ctx is None or not self._open:
            return
        symbol, headline = ctx
        dlg = _ArticleDialog(self, symbol, headline, article_text or "")
        dlg.exec()
