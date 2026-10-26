# Attribution — vendored chart runtime (P6-04)

- **TradingView Lightweight Charts™ v5.2.1** —
  `chart_assets/lwc/lightweight-charts.standalone.production.js`
- Copyright (c) TradingView, Inc. Licensed under the **Apache License 2.0**
  (https://www.apache.org/licenses/LICENSE-2.0); the full licence text ships
  in the vendored file's header comment.
- Source of the vendored build: https://unpkg.com/lightweight-charts@5.2.1/dist/lightweight-charts.standalone.production.js
- Vendored 2026-10-26 for offline (`ndt://`) use — no CDN or npm fetch at
  runtime (AC-D47.3). The pinned version is asserted by
  `tests/test_lwc_bridge.py` against `chart_assets/lwc/VERSION` and the
  vendored header.
